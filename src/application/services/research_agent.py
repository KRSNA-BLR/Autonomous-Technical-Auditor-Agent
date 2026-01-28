"""
Research Agent Service - Core autonomous research agent implementation.

This service orchestrates the research process using LangChain,
combining web search and text analysis tools to conduct comprehensive
technical research autonomously.
"""

import time
from dataclasses import dataclass
from typing import Any, cast

import structlog
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

from src.application.services.memory_manager import MemoryManager
from src.domain.entities.query import ResearchQuery
from src.domain.entities.report import ReportFormat, ReportSection, ResearchReport
from src.domain.entities.research import (
    ResearchResult,
    SearchResult,
    SourceCredibility,
)

logger = structlog.get_logger(__name__)


# ReAct Agent Prompt Template
REACT_PROMPT = """You are an expert technical research agent. Your goal is to conduct
thorough research on the given topic and provide accurate, well-sourced information.

CRITICAL LANGUAGE RULE:
- Detect the language of the question below
- You MUST respond ENTIRELY in the SAME language as the question
- If the question is in Spanish, your ENTIRE response must be in Spanish
- If the question is in English, your ENTIRE response must be in English
- This applies to ALL parts: thoughts, observations, and final answer

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must research
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to provide a comprehensive answer
Final Answer: the final answer with key findings and synthesis

Important guidelines:
1. Always search for multiple sources to verify information
2. Focus on recent and authoritative sources
3. Extract key technical details and best practices
4. Provide actionable insights when possible
5. Cite your sources in the final answer
6. RESPOND IN THE SAME LANGUAGE AS THE QUESTION

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


@dataclass
class AgentConfig:
    """Configuration for the research agent."""

    max_iterations: int = 10
    max_execution_time: int = 120  # seconds
    temperature: float = 0.3
    verbose: bool = True


class ResearchAgentService:
    """
    Autonomous research agent service.

    This service uses LangChain's ReAct agent pattern to conduct
    multi-step research by combining web search and text analysis tools.
    """

    def __init__(
        self,
        llm: BaseLanguageModel[Any],
        tools: list[BaseTool],
        memory_manager: MemoryManager,
        config: AgentConfig | None = None,
    ) -> None:
        """
        Initialize the research agent.

        Args:
            llm: The language model to use for reasoning
            tools: List of tools available to the agent
            memory_manager: Memory manager for conversation history
            config: Agent configuration options
        """
        self._llm = llm
        self._tools = tools
        self._memory = memory_manager
        self._config = config or AgentConfig()
        self._agent_executor = self._create_agent_executor()

        logger.info(
            "ResearchAgentService initialized",
            tools=[t.name for t in tools],
            max_iterations=self._config.max_iterations,
        )

    def _create_agent_executor(self) -> AgentExecutor:
        """Create the LangChain agent executor."""
        prompt = PromptTemplate.from_template(REACT_PROMPT)

        agent = create_react_agent(
            llm=self._llm,
            tools=self._tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=cast("Any", agent),
            tools=self._tools,
            verbose=self._config.verbose,
            max_iterations=self._config.max_iterations,
            max_execution_time=self._config.max_execution_time,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    async def research(self, query: ResearchQuery) -> ResearchResult:
        """
        Conduct autonomous research on the given query.

        Args:
            query: The research query to investigate

        Returns:
            ResearchResult with findings and synthesis
        """
        start_time = time.perf_counter()

        logger.info(
            "Starting research",
            query_id=str(query.id),
            question=query.question[:100],
            query_type=query.query_type.value,
        )

        # Create pending result
        result = ResearchResult.create_pending(query.id)

        try:
            # Build the research prompt with context
            research_prompt = self._build_research_prompt(query)

            # Execute the agent
            agent_response = await self._agent_executor.ainvoke({"input": research_prompt})

            # Process agent response
            search_results = self._extract_search_results(agent_response)
            key_findings = self._extract_key_findings(agent_response)
            synthesis = agent_response.get("output", "")

            # Calculate confidence based on sources and findings
            confidence = self._calculate_confidence(search_results, key_findings)

            # Calculate processing time
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)

            # Store in memory
            self._memory.add_interaction(
                query=query.question,
                response=synthesis,
                metadata={"query_id": str(query.id)},
            )

            # Update result with findings
            result = result.with_results(
                search_results=tuple(search_results),
                key_findings=tuple(key_findings),
                synthesis=synthesis,
                confidence_score=confidence,
                processing_time_ms=processing_time_ms,
            )

            logger.info(
                "Research completed",
                query_id=str(query.id),
                sources=len(search_results),
                findings=len(key_findings),
                confidence=confidence,
                time_ms=processing_time_ms,
            )

        except Exception as e:
            logger.error(
                "Research failed",
                query_id=str(query.id),
                error=str(e),
            )
            result = result.mark_failed(str(e))

        return result

    def _build_research_prompt(self, query: ResearchQuery) -> str:
        """Build a comprehensive research prompt."""
        prompt_parts = [f"Research Question: {query.question}"]

        if query.context:
            prompt_parts.append(f"\nAdditional Context: {query.context}")

        if query.keywords:
            prompt_parts.append(f"\nFocus Keywords: {', '.join(query.keywords)}")

        prompt_parts.append(f"\nResearch Type: {query.query_type.value}")
        prompt_parts.append(f"\nMaximum Sources: {query.max_sources}")

        # Add memory context if available
        recent_context = self._memory.get_relevant_context(query.question)
        if recent_context:
            prompt_parts.append(f"\nRelevant Previous Research:\n{recent_context}")

        return "\n".join(prompt_parts)

    def _extract_search_results(self, agent_response: dict[str, Any]) -> list[SearchResult]:
        """Extract search results from agent intermediate steps."""
        search_results: list[SearchResult] = []

        intermediate_steps = agent_response.get("intermediate_steps", [])

        for step in intermediate_steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                if hasattr(action, "tool") and "search" in action.tool.lower():
                    # Parse observation to extract results
                    results = self._parse_search_observation(str(observation))
                    search_results.extend(results)

        # Filter out irrelevant sources
        filtered_results = self._filter_irrelevant_sources(search_results)
        return filtered_results[:10]  # Limit to 10 results

    def _filter_irrelevant_sources(self, sources: list[SearchResult]) -> list[SearchResult]:
        """Filter out irrelevant or low-quality sources."""
        # Blocked domains - spam, unrelated, or non-research sites
        blocked_domains = [
            "zhihu.com",
            "baidu.com",
            "weibo.com",
            "qq.com",
            "whitepages.com",
            "yellowpages.com",
            "facebook.com",
            "instagram.com",
            "tiktok.com",
            "pinterest.com",
            "linkedin.com/in/",
            "twitter.com",
            "x.com",
        ]

        filtered = []
        for source in sources:
            url_lower = source.url.lower()

            # Skip blocked domains
            if any(blocked in url_lower for blocked in blocked_domains):
                logger.debug("Filtered blocked domain", url=source.url)
                continue

            # Skip if title has too many non-latin characters (likely wrong language)
            if not self._has_valid_latin_text(source.title):
                logger.debug("Filtered non-latin title", title=source.title[:50])
                continue

            # Skip if snippet has too many non-latin characters
            if source.snippet and not self._has_valid_latin_text(source.snippet):
                logger.debug("Filtered non-latin snippet", url=source.url)
                continue

            filtered.append(source)

        logger.info(
            "Filtered sources",
            original=len(sources),
            filtered=len(filtered),
        )
        return filtered

    def _has_valid_latin_text(self, text: str) -> bool:
        """Check if text contains mostly Latin/Spanish characters."""
        if not text or len(text) < 5:
            return False

        # Count Latin characters (basic + extended for Spanish/Portuguese/French)
        latin_count = 0
        for char in text:
            # Basic ASCII letters
            if (
                "A" <= char <= "Z"
                or "a" <= char <= "z"
                or "\u00c0" <= char <= "\u00ff"
                or char in " 0123456789"
            ):
                latin_count += 1

        # At least 50% should be Latin/neutral characters
        ratio = latin_count / len(text)
        return ratio > 0.5

    def _parse_search_observation(self, observation: str) -> list[SearchResult]:
        """Parse search observation string into SearchResult objects."""
        results: list[SearchResult] = []

        # Split by "Result" markers for robust parsing
        import re

        result_blocks = re.split(r"Result \d+:", observation)

        for block in result_blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            title = ""
            url = ""
            snippet = ""

            for line in lines:
                line = line.strip()
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                elif line.startswith("URL:") or line.startswith("Link:"):
                    # Handle URL: or just the URL after colon
                    url_part = line.split(":", 1)[-1].strip() if ":" in line else line
                    # Reconstruct full URL if it was split
                    if url_part.startswith("//") or url_part.startswith("/"):
                        url = "https:" + url_part
                    elif not url_part.startswith("http"):
                        url = "https://" + url_part
                    else:
                        url = url_part
                elif line.startswith("Snippet:") or line.startswith("Description:"):
                    snippet = line.split(":", 1)[-1].strip()
                elif not snippet and title and len(line) > 20:
                    # Capture any descriptive text as snippet
                    snippet = line

            if title:
                results.append(
                    SearchResult.create(
                        title=title,
                        url=url or "https://duckduckgo.com",
                        snippet=snippet or title,
                        credibility=self._assess_credibility(url),
                    )
                )

        logger.debug("Parsed search results", count=len(results))
        return results

    def _assess_credibility(self, url: str) -> SourceCredibility:
        """Assess source credibility based on URL domain."""
        high_credibility_domains = [
            "wikipedia.org",
            "nasa.gov",
            ".gov",
            ".edu",
            "nature.com",
            "sciencedirect.com",
            "ieee.org",
            "microsoft.com",
            "google.com",
            "github.com",
            "stackoverflow.com",
            "mozilla.org",
            "python.org",
        ]
        medium_credibility_domains = [
            "medium.com",
            "dev.to",
            "bbc.com",
            "cnn.com",
            "reuters.com",
            "techcrunch.com",
            "wired.com",
        ]

        url_lower = url.lower()

        for domain in high_credibility_domains:
            if domain in url_lower:
                return SourceCredibility.HIGH

        for domain in medium_credibility_domains:
            if domain in url_lower:
                return SourceCredibility.MEDIUM

        return SourceCredibility.MEDIUM

    def _extract_key_findings(self, agent_response: dict[str, Any]) -> list[str]:
        """Extract key findings from the agent response."""
        output = agent_response.get("output", "")
        findings: list[str] = []

        # Extract bullet points and numbered lists
        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            # Match bullet points or numbered items
            if (
                line.startswith("-")
                or line.startswith("•")
                or line.startswith("*")
                or line.startswith("→")
                or line.startswith("✓")
                or line.startswith("►")
                or (len(line) > 2 and line[0].isdigit() and line[1] in ".):-")
            ):
                # Remove leading bullet/number characters one by one
                chars_to_strip = set("-•*→✓►0123456789.):- ")
                finding = line
                while finding and finding[0] in chars_to_strip:
                    finding = finding[1:]
                finding = finding.strip()
                if finding and len(finding) > 15:
                    findings.append(finding)

        # If no bullet points found, try to extract key sentences
        if not findings:
            # Split by periods but keep sentence structure
            sentences = output.replace("\n", " ").split(". ")
            key_indicators = [
                "important",
                "key",
                "best",
                "recommend",
                "should",
                "must",
                "first",
                "principal",
                "main",
                "primary",
                "essential",
                "importante",
                "clave",
                "mejor",
                "recomienda",
                "debe",
                "primero",
                "principal",
                "esencial",
                "fundamental",
            ]
            for s in sentences:
                s = s.strip()
                if len(s) > 30 and any(kw in s.lower() for kw in key_indicators):
                    findings.append(s + "." if not s.endswith(".") else s)
                    if len(findings) >= 5:
                        break

        # If still no findings, extract first meaningful sentences
        if not findings and len(output) > 100:
            sentences = output.replace("\n", " ").split(". ")
            for s in sentences[:5]:
                s = s.strip()
                if len(s) > 40:
                    findings.append(s + "." if not s.endswith(".") else s)

        logger.debug("Extracted findings", count=len(findings))
        return findings[:10]  # Limit to 10 findings

    def _calculate_confidence(
        self,
        search_results: list[SearchResult],
        key_findings: list[str],
    ) -> float:
        """Calculate confidence score based on research quality."""
        score = 0.0

        # Base score for completing research (0.3)
        if search_results or key_findings:
            score += 0.3

        # Source quantity (max 0.35) - more generous scoring
        source_count = len(search_results)
        score += min(source_count * 0.07, 0.35)

        # Findings quantity (max 0.25)
        finding_count = len(key_findings)
        score += min(finding_count * 0.05, 0.25)

        # Source credibility bonus (max 0.1)
        high_cred_count = sum(1 for r in search_results if r.credibility == SourceCredibility.HIGH)
        score += min(high_cred_count * 0.03, 0.1)

        return min(score, 1.0)

    async def generate_report(
        self,
        research: ResearchResult,
        query: ResearchQuery,
        report_format: ReportFormat = ReportFormat.JSON,
    ) -> ResearchReport:
        """
        Generate a structured report from research results.

        Args:
            research: The research result to report on
            query: The original query
            report_format: Desired output format

        Returns:
            ResearchReport with formatted findings
        """
        logger.info("Generating report", research_id=str(research.id))

        # Create report sections
        sections = [
            ReportSection.create(
                title="Research Overview",
                content=f"This research investigated: {query.question}",
                order=1,
            ),
            ReportSection.create(
                title="Key Findings",
                content="\n".join(f"• {f}" for f in research.key_findings),
                order=2,
                sources=tuple(r.url for r in research.search_results[:5]),
            ),
            ReportSection.create(
                title="Analysis",
                content=research.synthesis,
                order=3,
            ),
        ]

        # Generate recommendations based on findings
        recommendations = self._generate_recommendations(research)

        report = ResearchReport.from_research(
            research=research,
            title=f"Research Report: {query.question[:50]}...",
            sections=tuple(sections),
            recommendations=tuple(recommendations),
            report_format=report_format,
        )

        logger.info(
            "Report generated",
            report_id=str(report.id),
            sections=len(sections),
            format=report_format.value,
        )

        return report

    def _generate_recommendations(self, research: ResearchResult) -> list[str]:
        """Generate actionable recommendations from research."""
        recommendations = []

        if research.confidence_score < 0.5:
            recommendations.append(
                "Consider conducting additional research with more specific queries"
            )

        if research.source_count < 3:
            recommendations.append("Verify findings with additional authoritative sources")

        if research.key_findings:
            recommendations.append(
                "Review key findings and prioritize implementation based on impact"
            )

        recommendations.append(
            "Document any decisions made based on this research for future reference"
        )

        return recommendations

    @property
    def tools(self) -> list[BaseTool]:
        """Get available tools."""
        return self._tools

    @property
    def memory(self) -> MemoryManager:
        """Get memory manager."""
        return self._memory
