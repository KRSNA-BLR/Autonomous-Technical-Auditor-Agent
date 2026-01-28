"""
Research Agent Service - Core autonomous research agent implementation.

This service orchestrates the research process using LangChain,
combining web search and text analysis tools to conduct comprehensive
technical research autonomously.
"""

import time
from dataclasses import dataclass
from typing import Any

import structlog
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from src.application.services.memory_manager import MemoryManager
from src.domain.entities.query import ResearchQuery
from src.domain.entities.report import ReportFormat, ReportSection, ResearchReport
from src.domain.entities.research import (
    ResearchResult,
    ResearchStatus,
    SearchResult,
    SourceCredibility,
)

logger = structlog.get_logger(__name__)


# ReAct Agent Prompt Template
REACT_PROMPT = """You are an expert technical research agent. Your goal is to conduct 
thorough research on the given topic and provide accurate, well-sourced information.

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
        llm: BaseLanguageModel,
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
            agent=agent,  # type: ignore
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
            agent_response = await self._agent_executor.ainvoke(
                {"input": research_prompt}
            )

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

    def _extract_search_results(
        self, agent_response: dict[str, Any]
    ) -> list[SearchResult]:
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

        return search_results[:10]  # Limit to 10 results

    def _parse_search_observation(self, observation: str) -> list[SearchResult]:
        """Parse search observation string into SearchResult objects."""
        results: list[SearchResult] = []

        # Simple parsing - in production, this would be more sophisticated
        lines = observation.split("\n")
        current_title = ""
        current_url = ""
        current_snippet = ""

        for line in lines:
            line = line.strip()
            if line.startswith("Title:"):
                if current_title and current_snippet:
                    results.append(
                        SearchResult.create(
                            title=current_title,
                            url=current_url or "https://example.com",
                            snippet=current_snippet,
                            credibility=SourceCredibility.MEDIUM,
                        )
                    )
                current_title = line.replace("Title:", "").strip()
                current_url = ""
                current_snippet = ""
            elif line.startswith("URL:") or line.startswith("Link:"):
                current_url = line.split(":", 1)[-1].strip()
            elif line.startswith("Snippet:") or line.startswith("Description:"):
                current_snippet = line.split(":", 1)[-1].strip()
            elif current_title and not current_snippet:
                current_snippet = line

        # Add last result
        if current_title and current_snippet:
            results.append(
                SearchResult.create(
                    title=current_title,
                    url=current_url or "https://example.com",
                    snippet=current_snippet,
                    credibility=SourceCredibility.MEDIUM,
                )
            )

        return results

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
                or (len(line) > 2 and line[0].isdigit() and line[1] in ".)")
            ):
                finding = line.lstrip("-•*0123456789.) ").strip()
                if finding and len(finding) > 20:
                    findings.append(finding)

        # If no bullet points found, try to extract key sentences
        if not findings:
            sentences = output.replace("\n", " ").split(". ")
            findings = [
                s.strip() + "."
                for s in sentences
                if len(s.strip()) > 50 and any(
                    kw in s.lower()
                    for kw in ["important", "key", "best", "recommend", "should", "must"]
                )
            ][:5]

        return findings[:10]  # Limit to 10 findings

    def _calculate_confidence(
        self,
        search_results: list[SearchResult],
        key_findings: list[str],
    ) -> float:
        """Calculate confidence score based on research quality."""
        score = 0.0

        # Source quantity (max 0.3)
        source_count = len(search_results)
        score += min(source_count * 0.06, 0.3)

        # Findings quantity (max 0.3)
        finding_count = len(key_findings)
        score += min(finding_count * 0.06, 0.3)

        # Source credibility (max 0.2)
        high_cred_count = sum(
            1 for r in search_results if r.credibility == SourceCredibility.HIGH
        )
        score += min(high_cred_count * 0.05, 0.2)

        # Base score for completing research (0.2)
        if search_results or key_findings:
            score += 0.2

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
            recommendations.append(
                "Verify findings with additional authoritative sources"
            )

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
