"""
Gemini LLM Adapter - Implementation of LLM port using Google Gemini API.

Google Gemini provides a generous FREE tier:
- gemini-2.0-flash: 1500 requests/day, 15 RPM, 1M TPM
- gemini-2.5-flash: 20 requests/day (limited!)

Get your free API key at: https://aistudio.google.com/apikey
"""

import asyncio
import json
import random
from typing import Any, ClassVar

import structlog
from langchain_google_genai import ChatGoogleGenerativeAI

from src.domain.ports.llm_port import (
    LLMConnectionError,
    LLMError,
    LLMPort,
    LLMRateLimitError,
    LLMResponse,
    LLMResponseError,
)

logger = structlog.get_logger(__name__)


class GeminiLLMAdapter(LLMPort):
    """
    Google Gemini API adapter implementing the LLM port.

    Uses Gemini's free tier with generous rate limits.
    Includes automatic retry with exponential backoff for rate limit errors.
    
    Recommended models for free tier:
    - gemini-2.0-flash: 1500 requests/day (RECOMMENDED)
    - gemini-2.5-flash: Only 20 requests/day (LIMITED!)
    """

    # Available models on Gemini free tier (ordered by free tier limits)
    AVAILABLE_MODELS: ClassVar[list[str]] = [
        "gemini-2.0-flash",      # 1500 req/day - RECOMMENDED
        "gemini-2.0-flash-lite", # 1500 req/day
        "gemini-1.5-flash",      # 1500 req/day
        "gemini-2.5-flash",      # 20 req/day - LIMITED!
        "gemini-2.5-pro",        # Limited
    ]
    
    # Retry configuration
    MAX_RETRIES: ClassVar[int] = 3
    BASE_DELAY: ClassVar[float] = 2.0  # seconds
    MAX_DELAY: ClassVar[float] = 60.0  # seconds

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",  # Changed default to higher-limit model
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the Gemini adapter.

        Args:
            api_key: Google API key (free at aistudio.google.com)
            model: Model to use (default: gemini-2.0-flash - 1500 req/day)
            temperature: Default temperature for generation
            max_tokens: Default max tokens for generation
            max_retries: Max retry attempts for rate limit errors
        """
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_retries = max_retries

        self._client = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            "GeminiLLMAdapter initialized",
            model=model,
            temperature=temperature,
            max_retries=max_retries,
        )

    def get_langchain_llm(self) -> ChatGoogleGenerativeAI:
        """
        Get the LangChain ChatGoogleGenerativeAI instance for use with agents.

        Returns:
            Configured ChatGoogleGenerativeAI instance
        """
        return self._client

    async def _execute_with_retry(
        self,
        operation: str,
        coro_func,
        *args,
        **kwargs,
    ):
        """
        Execute an async operation with exponential backoff retry.
        
        Args:
            operation: Name of the operation for logging
            coro_func: Async function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the operation
            
        Raises:
            LLMRateLimitError: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(self._max_retries + 1):
            try:
                return await coro_func(*args, **kwargs)
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                is_rate_limit = any(x in error_msg for x in [
                    "rate limit", "quota", "429", "too many requests",
                    "resource_exhausted"
                ])
                
                if not is_rate_limit:
                    # Not a rate limit error, don't retry
                    raise
                
                last_error = e
                
                if attempt < self._max_retries:
                    # Calculate delay with exponential backoff + jitter
                    delay = min(
                        self.BASE_DELAY * (2 ** attempt) + random.uniform(0, 1),
                        self.MAX_DELAY
                    )
                    
                    logger.warning(
                        f"Rate limit hit, retrying {operation}",
                        attempt=attempt + 1,
                        max_retries=self._max_retries,
                        delay_seconds=round(delay, 2),
                        error=str(e)[:100],
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All retries exhausted for {operation}",
                        attempts=self._max_retries + 1,
                        error=str(e),
                    )
        
        raise LLMRateLimitError(
            f"Rate limit exceeded after {self._max_retries + 1} attempts: {last_error}",
            last_error
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate text completion using Gemini with automatic retry.

        Args:
            prompt: The user prompt
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse with generated content
        """
        return await self._execute_with_retry(
            "generate",
            self._generate_internal,
            prompt,
            system_prompt,
            temperature,
            max_tokens,
        )

    async def _generate_internal(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Internal generate method without retry wrapper."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        # Create a new client with overridden parameters if needed
        client = self._client
        if temperature is not None or max_tokens is not None:
            client = ChatGoogleGenerativeAI(
                model=self._model,
                google_api_key=self._api_key,
                temperature=temperature or self._temperature,
                max_tokens=max_tokens or self._max_tokens,
            )

        response = await client.ainvoke(messages)

        # Extract token usage if available
        tokens_used = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_used = response.usage_metadata.get("total_tokens", 0)

        # Handle Gemini's content format (can be list or string)
        content = response.content
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
                elif isinstance(block, str):
                    text_parts.append(block)
            content = " ".join(text_parts)

        return LLMResponse(
            content=str(content),
            model=self._model,
            tokens_used=tokens_used,
            finish_reason=response.response_metadata.get("finish_reason", "STOP") if hasattr(response, "response_metadata") else "STOP",
            metadata=response.response_metadata if hasattr(response, "response_metadata") else {},
        )

    async def generate_structured(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output.

        Args:
            prompt: The user prompt
            output_schema: Expected JSON schema
            system_prompt: Optional system instructions

        Returns:
            Parsed dictionary matching the schema
        """
        schema_str = json.dumps(output_schema, indent=2)

        structured_system_prompt = (
            f"{system_prompt or ''}\n\n"
            f"You must respond with valid JSON matching this schema:\n"
            f"{schema_str}\n\n"
            f"Respond ONLY with the JSON object, no additional text."
        )

        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt=structured_system_prompt.strip(),
                temperature=0.3,  # Lower temperature for structured output
            )

            # Parse JSON from response
            content = response.content.strip()

            # Handle markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            result: dict[str, Any] = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            raise LLMResponseError(f"Failed to parse JSON response: {e}", e)

    async def analyze_text(
        self,
        text: str,
        analysis_type: str,
    ) -> dict[str, Any]:
        """
        Analyze text for specific attributes.

        Args:
            text: Text to analyze
            analysis_type: Type of analysis

        Returns:
            Analysis results dictionary
        """
        prompts = {
            "summary": "Summarize the following text in 2-3 sentences:",
            "keywords": "Extract 5-10 key terms from the following text:",
            "sentiment": "Analyze the sentiment (positive/negative/neutral) of:",
            "entities": "Extract named entities (people, places, organizations) from:",
        }

        prompt = f"{prompts.get(analysis_type, 'Analyze the following text:')}\n\n{text}"

        schema = {
            "analysis_type": analysis_type,
            "result": "string or array depending on analysis type",
            "confidence": "float between 0 and 1",
        }

        return await self.generate_structured(prompt, schema)

    async def health_check(self) -> bool:
        """
        Check if Gemini API is available.

        Returns:
            True if service is healthy
        """
        try:
            response = await self.generate(
                prompt="Say 'OK' if you're working.",
                max_tokens=10,
            )
            return bool(response.content)
        except Exception as e:
            logger.error("Gemini health check failed", error=str(e))
            return False
