"""
Text Analyzer Tool - LangChain tool for text analysis operations.

This tool provides text analysis capabilities including summarization,
key point extraction, and sentiment analysis using the LLM.
"""

from enum import Enum
from typing import Any

import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class AnalysisType(str, Enum):
    """Types of text analysis available."""

    SUMMARIZE = "summarize"
    KEY_POINTS = "key_points"
    SENTIMENT = "sentiment"
    TECHNICAL_TERMS = "technical_terms"
    PROS_CONS = "pros_cons"


class TextAnalysisInput(BaseModel):
    """Input schema for text analysis tool."""

    text: str = Field(description="The text to analyze")
    analysis_type: str = Field(
        default="summarize",
        description=(
            "Type of analysis: 'summarize', 'key_points', "
            "'sentiment', 'technical_terms', or 'pros_cons'"
        ),
    )


class TextAnalyzerTool(BaseTool):
    """
    LangChain tool for analyzing text content.

    Provides various text analysis capabilities powered by the LLM.
    """

    name: str = "text_analyzer"
    description: str = (
        "Analyze text content to extract insights. "
        "Can summarize text, extract key points, analyze sentiment, "
        "identify technical terms, or list pros and cons. "
        "Use analysis_type to specify what kind of analysis you need."
    )
    args_schema: type[BaseModel] = TextAnalysisInput
    llm: BaseLanguageModel | None = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def __init__(self, llm: BaseLanguageModel | None = None, **kwargs: Any) -> None:
        """Initialize the text analyzer with an optional LLM."""
        super().__init__(**kwargs)
        self.llm = llm

    def _get_analysis_prompt(self, text: str, analysis_type: str) -> str:
        """Generate the appropriate analysis prompt."""
        prompts = {
            "summarize": (
                f"Provide a concise summary of the following text in 2-3 sentences:\n\n{text}"
            ),
            "key_points": (
                f"Extract the key points from the following text as a bulleted list:\n\n{text}"
            ),
            "sentiment": (
                f"Analyze the sentiment of the following text. "
                f"Indicate if it's positive, negative, or neutral, "
                f"and explain why:\n\n{text}"
            ),
            "technical_terms": (
                f"Identify and explain the technical terms used in the following text:\n\n{text}"
            ),
            "pros_cons": (
                f"List the pros and cons discussed or implied in the following text:\n\n{text}"
            ),
        }
        return prompts.get(
            analysis_type,
            f"Analyze the following text:\n\n{text}",
        )

    def _run(self, text: str, analysis_type: str = "summarize") -> str:
        """
        Execute text analysis synchronously.

        Args:
            text: The text to analyze
            analysis_type: Type of analysis to perform

        Returns:
            Analysis results as a string
        """
        if not text or len(text.strip()) < 10:
            return "Error: Text is too short to analyze."

        logger.info(
            "Analyzing text",
            analysis_type=analysis_type,
            text_length=len(text),
        )

        # If LLM is available, use it for analysis
        if self.llm:
            try:
                prompt = self._get_analysis_prompt(text, analysis_type)
                response = self.llm.invoke(prompt)
                result = response.content if hasattr(response, "content") else str(response)
                logger.info("Analysis completed with LLM")
                return str(result)
            except Exception as e:
                logger.error("LLM analysis failed", error=str(e))
                # Fall through to rule-based analysis

        # Fallback: Rule-based analysis
        return self._rule_based_analysis(text, analysis_type)

    def _rule_based_analysis(self, text: str, analysis_type: str) -> str:
        """Perform rule-based text analysis as fallback."""
        if analysis_type == "summarize":
            # Simple extractive summary - first and last sentences
            sentences = text.replace("\n", " ").split(". ")
            if len(sentences) <= 3:
                return text
            summary = ". ".join([sentences[0], sentences[-1]])
            return f"Summary: {summary}."

        elif analysis_type == "key_points":
            # Extract sentences with key indicators
            sentences = text.replace("\n", " ").split(". ")
            key_indicators = [
                "important",
                "key",
                "main",
                "critical",
                "essential",
                "primary",
                "significant",
                "must",
                "should",
            ]
            key_points = []
            for sentence in sentences:
                if any(ind in sentence.lower() for ind in key_indicators):
                    key_points.append(f"• {sentence.strip()}")
            if not key_points:
                # Just take first 3 sentences
                key_points = [f"• {s.strip()}" for s in sentences[:3]]
            return "Key Points:\n" + "\n".join(key_points[:5])

        elif analysis_type == "sentiment":
            # Simple sentiment based on positive/negative word counts
            positive_words = [
                "good",
                "great",
                "excellent",
                "best",
                "amazing",
                "wonderful",
                "fantastic",
                "love",
                "like",
                "helpful",
                "useful",
                "benefit",
            ]
            negative_words = [
                "bad",
                "poor",
                "worst",
                "terrible",
                "hate",
                "dislike",
                "problem",
                "issue",
                "difficult",
                "fail",
                "error",
                "wrong",
            ]
            text_lower = text.lower()
            pos_count = sum(1 for w in positive_words if w in text_lower)
            neg_count = sum(1 for w in negative_words if w in text_lower)

            if pos_count > neg_count * 1.5:
                sentiment = "Positive"
            elif neg_count > pos_count * 1.5:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"

            return f"Sentiment: {sentiment} (positive indicators: {pos_count}, negative indicators: {neg_count})"

        elif analysis_type == "technical_terms":
            # Extract capitalized terms and common tech patterns
            words = text.split()
            tech_patterns = ["API", "SDK", "HTTP", "JSON", "SQL", "REST", "GraphQL"]
            terms = set()
            for word in words:
                clean_word = word.strip(".,!?()[]{}\"'")
                if (clean_word.isupper() and len(clean_word) > 2) or clean_word in tech_patterns:
                    terms.add(clean_word)
            if terms:
                return "Technical Terms Found: " + ", ".join(sorted(terms))
            return "No specific technical terms identified."

        elif analysis_type == "pros_cons":
            text_lower = text.lower()
            # Look for pros/cons indicators
            pros = []
            cons = []
            sentences = text.replace("\n", " ").split(". ")
            for sentence in sentences:
                s_lower = sentence.lower()
                if any(w in s_lower for w in ["advantage", "benefit", "pro", "good", "strength"]):
                    pros.append(sentence.strip())
                elif any(
                    w in s_lower for w in ["disadvantage", "drawback", "con", "issue", "weakness"]
                ):
                    cons.append(sentence.strip())

            result = []
            if pros:
                result.append("Pros:\n" + "\n".join(f"+ {p}" for p in pros[:3]))
            if cons:
                result.append("Cons:\n" + "\n".join(f"- {c}" for c in cons[:3]))
            return "\n\n".join(result) if result else "No clear pros or cons identified."

        return f"Analysis type '{analysis_type}' not supported."

    async def _arun(self, text: str, analysis_type: str = "summarize") -> str:
        """Execute text analysis asynchronously."""
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(None, self._run, text, analysis_type)
