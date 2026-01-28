"""
Search Port - Abstract interface for web search operations.

This port defines the contract for any search adapter implementation,
enabling easy swapping between different search providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class WebSearchResult:
    """
    Immutable web search result.

    Attributes:
        title: Page title
        url: Page URL
        snippet: Text snippet from the page
        source: Search provider that returned this result
        position: Position in search results
        retrieved_at: When the result was fetched
    """

    title: str
    url: str
    snippet: str
    source: str
    position: int
    retrieved_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "position": self.position,
            "retrieved_at": self.retrieved_at.isoformat(),
        }


class SearchPort(ABC):
    """
    Abstract port for web search operations.

    This interface allows the application to remain agnostic about
    the specific search provider being used.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
        region: str = "wt-wt",
    ) -> list[WebSearchResult]:
        """
        Perform a web search.

        Args:
            query: The search query string
            max_results: Maximum number of results to return
            region: Region code for localized results

        Returns:
            List of WebSearchResult objects

        Raises:
            SearchError: If the search operation fails
        """
        ...

    @abstractmethod
    async def search_news(
        self,
        query: str,
        max_results: int = 5,
        time_range: str = "w",
    ) -> list[WebSearchResult]:
        """
        Search for news articles.

        Args:
            query: The search query
            max_results: Maximum results
            time_range: Time range (d=day, w=week, m=month)

        Returns:
            List of news results
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the search service is available.

        Returns:
            True if service is healthy
        """
        ...


class SearchError(Exception):
    """Base exception for search-related errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class SearchRateLimitError(SearchError):
    """Raised when search rate limit is exceeded."""

    pass


class SearchConnectionError(SearchError):
    """Raised when connection to search service fails."""

    pass
