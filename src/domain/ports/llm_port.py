"""
LLM Port - Abstract interface for Language Model interactions.

This port defines the contract that any LLM adapter must implement,
following the Ports and Adapters (Hexagonal) architecture pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """
    Immutable response from the LLM.

    Attributes:
        content: The generated text content
        model: The model that generated the response
        tokens_used: Number of tokens consumed
        finish_reason: Why the generation stopped
        metadata: Additional response metadata
    """

    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: dict[str, Any]

    @property
    def is_complete(self) -> bool:
        """Check if generation completed normally."""
        return self.finish_reason in ("stop", "end_turn", "complete")


class LLMPort(ABC):
    """
    Abstract port for LLM interactions.

    This interface defines the contract that all LLM adapters must implement.
    Following the Dependency Inversion Principle, the domain layer depends on
    this abstraction, not on concrete implementations.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """
        Generate text completion from the LLM.

        Args:
            prompt: The user prompt to send
            system_prompt: Optional system instructions
            temperature: Creativity parameter (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with the generated content

        Raises:
            LLMError: If generation fails
        """
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output from the LLM.

        Args:
            prompt: The user prompt
            output_schema: JSON schema for the expected output
            system_prompt: Optional system instructions

        Returns:
            Parsed dictionary matching the schema

        Raises:
            LLMError: If generation or parsing fails
        """
        ...

    @abstractmethod
    async def analyze_text(
        self,
        text: str,
        analysis_type: str,
    ) -> dict[str, Any]:
        """
        Analyze text for specific attributes.

        Args:
            text: Text to analyze
            analysis_type: Type of analysis (sentiment, summary, keywords, etc.)

        Returns:
            Analysis results as a dictionary
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        ...


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class LLMConnectionError(LLMError):
    """Raised when connection to LLM service fails."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""

    pass


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or cannot be parsed."""

    pass
