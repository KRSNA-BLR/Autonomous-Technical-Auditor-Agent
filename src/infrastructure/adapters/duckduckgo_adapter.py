"""
DuckDuckGo Search Adapter - Implementation of Search port using DuckDuckGo.

DuckDuckGo provides FREE, unlimited search without requiring an API key.
This makes it perfect for open-source projects and portfolio demos.
"""

from datetime import datetime
from typing import Any

import structlog

from src.domain.ports.search_port import (
    SearchConnectionError,
    SearchError,
    SearchPort,
    SearchRateLimitError,
    WebSearchResult,
)

logger = structlog.get_logger(__name__)


class DuckDuckGoAdapter(SearchPort):
    """
    DuckDuckGo search adapter implementing the Search port.

    Uses the duckduckgo-search library for free, unlimited searches
    without requiring any API key.
    """

    def __init__(self, timeout: int = 10) -> None:
        """
        Initialize the DuckDuckGo adapter.

        Args:
            timeout: Request timeout in seconds
        """
        self._timeout = timeout
        logger.info("DuckDuckGoAdapter initialized", timeout=timeout)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        region: str = "us-en",
    ) -> list[WebSearchResult]:
        """
        Perform a web search using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Maximum results to return
            region: Region code (us-en = United States English)

        Returns:
            List of WebSearchResult objects
        """
        import asyncio

        try:
            from duckduckgo_search import DDGS

            logger.info(
                "Executing DuckDuckGo search",
                query=query,
                max_results=max_results,
            )

            # Run synchronous search in executor
            def do_search() -> list[dict[str, Any]]:
                with DDGS() as ddgs:
                    return list(
                        ddgs.text(
                            query,
                            region=region,
                            max_results=max_results,
                        )
                    )

            results = await asyncio.get_event_loop().run_in_executor(
                None, do_search
            )

            search_results = [
                WebSearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", r.get("link", "")),
                    snippet=r.get("body", r.get("snippet", "")),
                    source="duckduckgo",
                    position=i + 1,
                    retrieved_at=datetime.now(),
                )
                for i, r in enumerate(results)
            ]

            logger.info(
                "Search completed",
                results_count=len(search_results),
            )

            return search_results

        except ImportError:
            raise SearchError(
                "duckduckgo-search package not installed. "
                "Run: pip install duckduckgo-search"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg:
                raise SearchRateLimitError(f"Rate limited: {e}", e)
            elif "connection" in error_msg or "timeout" in error_msg:
                raise SearchConnectionError(f"Connection failed: {e}", e)
            else:
                raise SearchError(f"Search failed: {e}", e)

    async def search_news(
        self,
        query: str,
        max_results: int = 5,
        time_range: str = "w",
    ) -> list[WebSearchResult]:
        """
        Search for news articles using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum results
            time_range: Time range (d=day, w=week, m=month)

        Returns:
            List of news results
        """
        import asyncio

        try:
            from duckduckgo_search import DDGS

            logger.info("Executing DuckDuckGo news search", query=query)

            def do_news_search() -> list[dict[str, Any]]:
                with DDGS() as ddgs:
                    return list(
                        ddgs.news(
                            query,
                            timelimit=time_range,
                            max_results=max_results,
                        )
                    )

            results = await asyncio.get_event_loop().run_in_executor(
                None, do_news_search
            )

            return [
                WebSearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", r.get("link", "")),
                    snippet=r.get("body", r.get("excerpt", "")),
                    source=r.get("source", "duckduckgo_news"),
                    position=i + 1,
                    retrieved_at=datetime.now(),
                )
                for i, r in enumerate(results)
            ]

        except Exception as e:
            raise SearchError(f"News search failed: {e}", e)

    async def health_check(self) -> bool:
        """
        Check if DuckDuckGo search is available.

        Returns:
            True if service is working
        """
        try:
            results = await self.search("test", max_results=1)
            return len(results) > 0
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
