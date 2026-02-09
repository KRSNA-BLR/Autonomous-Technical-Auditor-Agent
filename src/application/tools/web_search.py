"""
Web Search Tool - LangChain tool for web search operations.

This tool wraps the DDGS metasearch library to provide web search capabilities
to the research agent. DDGS aggregates results from multiple engines
(Bing, Brave, Google, DuckDuckGo, etc.) - free, no API key required.

Library: https://pypi.org/project/ddgs/
"""

import asyncio

import structlog
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""

    query: str = Field(description="The search query to execute")
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return",
        ge=1,
        le=10,
    )


class WebSearchTool(BaseTool):
    """
    LangChain tool for performing web searches.

    Uses DDGS (Dux Distributed Global Search) as the search backend.
    Aggregates results from Bing, Brave, Google, DuckDuckGo, and more.
    Free, no API key required.
    """

    name: str = "web_search"
    description: str = (
        "Search the web for current information on any topic. "
        "Use this tool to find recent articles, documentation, "
        "tutorials, and technical resources. "
        "Input should be a clear search query."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """
        Execute a synchronous web search.

        Args:
            query: The search query
            max_results: Maximum results to return

        Returns:
            Formatted search results string
        """
        try:
            from ddgs import DDGS

            logger.info("Executing web search", query=query, max_results=max_results)

            ddgs = DDGS()
            search_results = ddgs.text(
                query,
                max_results=max_results,
                region="us-en",
            )

            results = []
            for i, result in enumerate(search_results, 1):
                results.append(
                    f"Result {i}:\n"
                    f"Title: {result.get('title', 'N/A')}\n"
                    f"URL: {result.get('href', 'N/A')}\n"
                    f"Snippet: {result.get('body', 'N/A')}\n"
                )

            if not results:
                return "No results found for the query."

            logger.info("Search completed", results_count=len(results))
            return "\n".join(results)

        except ImportError:
            logger.error("ddgs not installed, run: pip install ddgs")
            return "Error: Search functionality not available. Install ddgs: pip install ddgs"
        except Exception as e:
            logger.error("Search failed", error=str(e))
            return f"Error performing search: {e!s}"

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """
        Execute an asynchronous web search.

        Args:
            query: The search query
            max_results: Maximum results to return

        Returns:
            Formatted search results string
        """
        return await asyncio.get_event_loop().run_in_executor(None, self._run, query, max_results)


class NewsSearchTool(BaseTool):
    """
    LangChain tool for searching news articles.

    Uses DDGS News search for recent news and developments.
    Aggregates from Bing, DuckDuckGo, Yahoo news backends.
    """

    name: str = "news_search"
    description: str = (
        "Search for recent news articles and developments. "
        "Use this tool when you need current events, recent announcements, "
        "or the latest information on a topic. "
        "Input should be a news-related search query."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """Execute a synchronous news search."""
        try:
            from ddgs import DDGS

            logger.info("Executing news search", query=query)

            ddgs = DDGS()
            news_results = ddgs.news(
                query,
                max_results=max_results,
                region="us-en",
            )

            results = []
            for i, result in enumerate(news_results, 1):
                results.append(
                    f"News {i}:\n"
                    f"Title: {result.get('title', 'N/A')}\n"
                    f"Source: {result.get('source', 'N/A')}\n"
                    f"URL: {result.get('url', 'N/A')}\n"
                    f"Published: {result.get('date', 'N/A')}\n"
                    f"Summary: {result.get('body', 'N/A')}\n"
                )

            if not results:
                return "No news articles found for the query."

            return "\n".join(results)

        except Exception as e:
            logger.error("News search failed", error=str(e))
            return f"Error performing news search: {e!s}"

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Execute an asynchronous news search."""
        return await asyncio.get_event_loop().run_in_executor(None, self._run, query, max_results)
