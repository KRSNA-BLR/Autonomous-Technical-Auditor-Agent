"""
Groq LLM Adapter - Implementation of LLM port using Groq API.

Groq provides FREE API access to Llama 3, Mixtral, and other models
with extremely fast inference. Get your free API key at:
https://console.groq.com/keys
"""

import json
from typing import Any, ClassVar

import structlog
from langchain_groq import ChatGroq
from pydantic import SecretStr

from src.domain.ports.llm_port import (
    LLMConnectionError,
    LLMError,
    LLMPort,
    LLMRateLimitError,
    LLMResponse,
    LLMResponseError,
)

logger = structlog.get_logger(__name__)


class GroqLLMAdapter(LLMPort):
    """
    Groq API adapter implementing the LLM port.

    Uses Groq's free tier for fast inference with open-source models.
    Supports Llama 3, Mixtral, and other models.
    """

    # Available models on Groq free tier
    AVAILABLE_MODELS: ClassVar[list[str]] = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        """
        Initialize the Groq adapter.

        Args:
            api_key: Groq API key (free at console.groq.com)
            model: Model to use
            temperature: Default temperature for generation
            max_tokens: Default max tokens for generation
        """
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

        self._client = ChatGroq(
            api_key=SecretStr(api_key),
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            "GroqLLMAdapter initialized",
            model=model,
            temperature=temperature,
        )

    def get_langchain_llm(self) -> ChatGroq:
        """
        Get the LangChain ChatGroq instance for use with agents.

        Returns:
            Configured ChatGroq instance
        """
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate text completion using Groq.

        Args:
            prompt: The user prompt
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse with generated content
        """
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            # Create a new client with overridden parameters if needed
            client = self._client
            if temperature is not None or max_tokens is not None:
                client = ChatGroq(
                    api_key=SecretStr(self._api_key),
                    model=self._model,
                    temperature=temperature or self._temperature,
                    max_tokens=max_tokens or self._max_tokens,
                )

            response = await client.ainvoke(messages)

            # Extract token usage if available
            tokens_used = 0
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)

            return LLMResponse(
                content=str(response.content),
                model=self._model,
                tokens_used=tokens_used,
                finish_reason=response.response_metadata.get("finish_reason", "stop"),
                metadata=response.response_metadata or {},
            )

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg:
                raise LLMRateLimitError(f"Rate limit exceeded: {e}", e)
            elif "connection" in error_msg or "timeout" in error_msg:
                raise LLMConnectionError(f"Connection failed: {e}", e)
            else:
                raise LLMError(f"Generation failed: {e}", e)

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
        Check if Groq API is available.

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
            logger.error("Health check failed", error=str(e))
            return False
