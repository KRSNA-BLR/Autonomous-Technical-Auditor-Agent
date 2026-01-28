"""
API Dependencies - Dependency injection for FastAPI routes.

This module provides dependency injection functions for
services, adapters, and configuration throughout the API.
"""

from functools import lru_cache
from typing import Annotated

import structlog
from fastapi import Depends
from langchain_core.tools import BaseTool
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.application.services.memory_manager import MemoryManager
from src.application.services.research_agent import AgentConfig, ResearchAgentService
from src.application.services.sqlite_memory import SQLiteMemoryManager
from src.application.tools.text_analyzer import TextAnalyzerTool
from src.application.tools.web_search import NewsSearchTool, WebSearchTool
from src.infrastructure.adapters.groq_adapter import GroqLLMAdapter

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Groq Configuration (FREE API key from console.groq.com)
    groq_api_key: str = ""

    # LLM Model Selection
    llm_model: str = "llama-3.3-70b-versatile"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Agent Configuration
    agent_max_iterations: int = 15
    agent_memory_size: int = 100
    default_max_sources: int = 8

    # Memory Database
    memory_db_path: str = "./data/memory.db"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings instance loaded from environment
    """
    return Settings()


# Memory manager singleton
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """
    Get or create the memory manager singleton.

    Returns:
        SQLiteMemoryManager instance for persistent storage
    """
    global _memory_manager
    if _memory_manager is None:
        settings = get_settings()
        _memory_manager = SQLiteMemoryManager(
            db_path=settings.memory_db_path,
            max_entries=settings.agent_memory_size,
        )
        logger.info(
            "SQLiteMemoryManager initialized",
            db_path=settings.memory_db_path,
            max_entries=settings.agent_memory_size,
        )
    return _memory_manager


def get_llm_adapter(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GroqLLMAdapter:
    """
    Get the LLM adapter instance.

    Args:
        settings: Application settings

    Returns:
        Configured GroqLLMAdapter
    """
    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Get your FREE API key at: https://console.groq.com/keys"
        )

    return GroqLLMAdapter(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
    )


def get_tools(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[BaseTool]:
    """
    Get the list of tools available to the agent.

    Args:
        settings: Application settings

    Returns:
        List of configured tools
    """
    # Initialize LLM for text analyzer if API key is available
    llm = None
    if settings.groq_api_key:
        adapter = GroqLLMAdapter(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
        )
        llm = adapter.get_langchain_llm()

    tools: list[BaseTool] = [
        WebSearchTool(),
        NewsSearchTool(),
        TextAnalyzerTool(llm=llm),
    ]

    logger.info("Tools initialized", tools=[t.name for t in tools])
    return tools


def get_research_agent(
    settings: Annotated[Settings, Depends(get_settings)],
    llm_adapter: Annotated[GroqLLMAdapter, Depends(get_llm_adapter)],
    tools: Annotated[list[BaseTool], Depends(get_tools)],
    memory: Annotated[MemoryManager, Depends(get_memory_manager)],
) -> ResearchAgentService:
    """
    Get the research agent service.

    Args:
        settings: Application settings
        llm_adapter: LLM adapter instance
        tools: Available tools
        memory: Memory manager

    Returns:
        Configured ResearchAgentService
    """
    config = AgentConfig(
        max_iterations=settings.agent_max_iterations,
        verbose=settings.api_debug,
    )

    return ResearchAgentService(
        llm=llm_adapter.get_langchain_llm(),
        tools=tools,
        memory_manager=memory,
        config=config,
    )
