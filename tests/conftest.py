"""
Pytest configuration and shared fixtures.
"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture
def sample_research_request() -> dict:
    """Provide a sample research request for testing."""
    return {
        "question": "What are the best practices for FastAPI in production?",
        "context": "Focus on performance and security",
        "query_type": "technical",
        "priority": "high",
        "max_sources": 5,
        "keywords": ["FastAPI", "production", "performance"],
    }


@pytest.fixture
def sample_search_results() -> list[dict]:
    """Provide sample search results for testing."""
    return [
        {
            "title": "FastAPI Documentation",
            "url": "https://fastapi.tiangolo.com/",
            "snippet": "FastAPI is a modern, fast web framework for building APIs...",
        },
        {
            "title": "FastAPI Best Practices",
            "url": "https://example.com/fastapi-best-practices",
            "snippet": "Learn the best practices for building production-ready APIs...",
        },
    ]
