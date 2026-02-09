"""
LLM Factory - Factory pattern for creating LLM adapters with fallback support.

Provides automatic failover between Gemini and Groq to ensure reliability.
"""

from enum import StrEnum
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel

from src.domain.ports.llm_port import LLMPort, LLMResponse

logger = structlog.get_logger(__name__)


class LLMProvider(StrEnum):
    """Supported LLM providers."""

    GEMINI = "gemini"
    GROQ = "groq"
    AUTO = "auto"  # Automatic with fallback


class LLMFactory:
    """
    Factory for creating LLM adapters with optional fallback support.

    Default strategy (AUTO):
    1. Try Gemini (free tier with generous limits - 1500 req/day with gemini-2.0-flash)
    2. Fallback to Groq if Gemini fails (rate limit or other errors)

    Includes automatic retry with exponential backoff for rate limits.
    """

    def __init__(
        self,
        provider: LLMProvider | str = LLMProvider.AUTO,
        # Gemini config
        google_api_key: str | None = None,
        gemini_model: str = "gemini-2.0-flash",  # Changed default - 1500 req/day
        # Groq config
        groq_api_key: str | None = None,
        groq_model: str = "llama-3.3-70b-versatile",
        # Common config
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        """
        Initialize the LLM factory.

        Args:
            provider: Which provider to use (gemini, groq, or auto)
            google_api_key: API key for Google Gemini
            gemini_model: Gemini model to use
            groq_api_key: API key for Groq
            groq_model: Groq model to use
            temperature: Default temperature
            max_tokens: Default max tokens
        """
        self._provider = LLMProvider(provider) if isinstance(provider, str) else provider
        self._google_api_key = google_api_key
        self._gemini_model = gemini_model
        self._groq_api_key = groq_api_key
        self._groq_model = groq_model
        self._temperature = temperature
        self._max_tokens = max_tokens

        self._primary_adapter: LLMPort | None = None
        self._fallback_adapter: LLMPort | None = None

        logger.info(
            "LLMFactory initialized",
            provider=self._provider.value,
            gemini_available=bool(google_api_key),
            groq_available=bool(groq_api_key),
        )

    def _create_gemini_adapter(self) -> "LLMPort | None":
        """Create Gemini adapter if API key is available."""
        if not self._google_api_key:
            logger.warning("Gemini API key not configured")
            return None

        try:
            from src.infrastructure.adapters.gemini_adapter import GeminiLLMAdapter

            adapter = GeminiLLMAdapter(
                api_key=self._google_api_key,
                model=self._gemini_model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            logger.info("Gemini adapter created successfully", model=self._gemini_model)
            return adapter
        except Exception as e:
            logger.error("Failed to create Gemini adapter", error=str(e))
            return None

    def _create_groq_adapter(self) -> "LLMPort | None":
        """Create Groq adapter if API key is available."""
        if not self._groq_api_key:
            logger.warning("Groq API key not configured")
            return None

        try:
            from src.infrastructure.adapters.groq_adapter import GroqLLMAdapter

            adapter = GroqLLMAdapter(
                api_key=self._groq_api_key,
                model=self._groq_model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            logger.info("Groq adapter created successfully", model=self._groq_model)
            return adapter
        except Exception as e:
            logger.error("Failed to create Groq adapter", error=str(e))
            return None

    def create_adapter(self) -> LLMPort:
        """
        Create an LLM adapter based on the configured provider.

        For AUTO mode, creates primary (Gemini) and fallback (Groq) adapters.

        Returns:
            LLMPort adapter ready to use

        Raises:
            ValueError: If no valid adapter could be created
        """
        if self._provider == LLMProvider.GEMINI:
            adapter = self._create_gemini_adapter()
            if adapter:
                return adapter
            raise ValueError("Failed to create Gemini adapter - check GOOGLE_API_KEY")

        elif self._provider == LLMProvider.GROQ:
            adapter = self._create_groq_adapter()
            if adapter:
                return adapter
            raise ValueError("Failed to create Groq adapter - check GROQ_API_KEY")

        else:  # AUTO mode with fallback
            return self._create_adapter_with_fallback()

    def _create_adapter_with_fallback(self) -> LLMPort:
        """
        Create adapter with fallback support.

        Priority:
        1. Gemini (generous free tier)
        2. Groq (limited free tier)

        Returns:
            FallbackLLMAdapter wrapping primary and fallback adapters
        """
        self._primary_adapter = self._create_gemini_adapter()
        self._fallback_adapter = self._create_groq_adapter()

        if self._primary_adapter and self._fallback_adapter:
            logger.info(
                "Created adapter with fallback",
                primary="gemini",
                fallback="groq",
            )
            return FallbackLLMAdapter(
                primary=self._primary_adapter,
                fallback=self._fallback_adapter,
            )
        elif self._primary_adapter:
            logger.warning("Only Gemini available, no fallback configured")
            return self._primary_adapter
        elif self._fallback_adapter:
            logger.warning("Only Groq available, using as primary")
            return self._fallback_adapter
        else:
            raise ValueError("No LLM provider configured. Set GOOGLE_API_KEY or GROQ_API_KEY")


class FallbackLLMAdapter(LLMPort):
    """
    LLM adapter with automatic fallback on failure.

    Wraps a primary and fallback adapter, automatically switching
    when rate limits or errors occur.
    """

    def __init__(self, primary: LLMPort, fallback: LLMPort) -> None:
        """
        Initialize the fallback adapter.

        Args:
            primary: Primary LLM adapter (tried first)
            fallback: Fallback adapter (used on primary failure)
        """
        self._primary = primary
        self._fallback = fallback
        self._using_fallback = False

        logger.info("FallbackLLMAdapter initialized")

    def get_langchain_llm(self) -> BaseChatModel:
        """Get the LangChain LLM instance."""
        if self._using_fallback:
            return self._fallback.get_langchain_llm()
        return self._primary.get_langchain_llm()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate with automatic fallback on failure."""
        from src.domain.ports.llm_port import LLMError, LLMRateLimitError

        try:
            if not self._using_fallback:
                return await self._primary.generate(prompt, system_prompt, temperature, max_tokens)
        except (LLMRateLimitError, LLMError) as e:
            logger.warning(
                "Primary LLM failed, switching to fallback",
                error=str(e),
            )
            self._using_fallback = True

        # Try fallback
        try:
            return await self._fallback.generate(prompt, system_prompt, temperature, max_tokens)
        except Exception:
            # If fallback also fails, try to reset to primary next time
            self._using_fallback = False
            raise

    async def generate_structured(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured output with fallback."""
        from src.domain.ports.llm_port import LLMError, LLMRateLimitError

        try:
            if not self._using_fallback:
                return await self._primary.generate_structured(prompt, output_schema, system_prompt)
        except (LLMRateLimitError, LLMError) as e:
            logger.warning(
                "Primary LLM failed on structured generation, switching to fallback",
                error=str(e),
            )
            self._using_fallback = True

        return await self._fallback.generate_structured(prompt, output_schema, system_prompt)

    async def analyze_text(self, text: str, analysis_type: str) -> dict[str, Any]:
        """Analyze text with fallback."""
        from src.domain.ports.llm_port import LLMError, LLMRateLimitError

        try:
            if not self._using_fallback:
                return await self._primary.analyze_text(text, analysis_type)
        except (LLMRateLimitError, LLMError) as e:
            logger.warning(
                "Primary LLM failed on text analysis, switching to fallback",
                error=str(e),
            )
            self._using_fallback = True

        return await self._fallback.analyze_text(text, analysis_type)

    async def health_check(self) -> bool:
        """Check health of available adapters."""
        primary_healthy = await self._primary.health_check()
        fallback_healthy = await self._fallback.health_check()

        logger.info(
            "Health check completed",
            primary_healthy=primary_healthy,
            fallback_healthy=fallback_healthy,
        )

        # If primary is healthy, reset to using primary
        if primary_healthy and self._using_fallback:
            logger.info("Primary recovered, resetting to primary")
            self._using_fallback = False

        return primary_healthy or fallback_healthy
