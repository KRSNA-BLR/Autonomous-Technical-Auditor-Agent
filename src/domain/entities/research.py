"""
Research Entity - Represents the results of a research operation.

This entity contains the structured data collected during research,
including individual search results and aggregated findings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class SourceCredibility(StrEnum):
    """Credibility levels for research sources."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ResearchStatus(StrEnum):
    """Status of the research process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class SearchResult:
    """
    Immutable entity representing a single search result.

    Attributes:
        title: Title of the source
        url: URL of the source
        snippet: Text snippet from the source
        credibility: Assessed credibility of the source
        retrieved_at: When the result was retrieved
    """

    title: str
    url: str
    snippet: str
    credibility: SourceCredibility = SourceCredibility.UNKNOWN
    retrieved_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate the search result."""
        if not self.title:
            raise ValueError("Title cannot be empty")
        if not self.url:
            raise ValueError("URL cannot be empty")

    @classmethod
    def create(
        cls,
        title: str,
        url: str,
        snippet: str,
        credibility: SourceCredibility = SourceCredibility.UNKNOWN,
    ) -> "SearchResult":
        """Factory method to create a SearchResult."""
        return cls(
            title=title.strip(),
            url=url.strip(),
            snippet=snippet.strip(),
            credibility=credibility,
            retrieved_at=datetime.now(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "credibility": self.credibility.value,
            "retrieved_at": self.retrieved_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ResearchResult:
    """
    Immutable entity representing the complete research result.

    Attributes:
        id: Unique identifier
        query_id: Reference to the original query
        status: Current status of the research
        search_results: Collection of individual search results
        key_findings: Extracted key findings
        synthesis: Synthesized analysis of all findings
        confidence_score: Confidence in the research quality (0-1)
        processing_time_ms: Time taken to process in milliseconds
        created_at: When the research was created
        completed_at: When the research was completed
    """

    id: UUID
    query_id: UUID
    status: ResearchStatus
    search_results: tuple[SearchResult, ...]
    key_findings: tuple[str, ...]
    synthesis: str
    confidence_score: float
    processing_time_ms: int
    created_at: datetime
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the research result."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        if self.processing_time_ms < 0:
            raise ValueError("Processing time cannot be negative")

    @classmethod
    def create_pending(cls, query_id: UUID) -> "ResearchResult":
        """Create a pending research result."""
        return cls(
            id=uuid4(),
            query_id=query_id,
            status=ResearchStatus.PENDING,
            search_results=(),
            key_findings=(),
            synthesis="",
            confidence_score=0.0,
            processing_time_ms=0,
            created_at=datetime.now(),
            completed_at=None,
        )

    def with_results(
        self,
        search_results: tuple[SearchResult, ...],
        key_findings: tuple[str, ...],
        synthesis: str,
        confidence_score: float,
        processing_time_ms: int,
    ) -> "ResearchResult":
        """Create a completed research result with findings."""
        return ResearchResult(
            id=self.id,
            query_id=self.query_id,
            status=ResearchStatus.COMPLETED,
            search_results=search_results,
            key_findings=key_findings,
            synthesis=synthesis,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            created_at=self.created_at,
            completed_at=datetime.now(),
        )

    def mark_failed(self, error_message: str) -> "ResearchResult":
        """Create a failed research result."""
        return ResearchResult(
            id=self.id,
            query_id=self.query_id,
            status=ResearchStatus.FAILED,
            search_results=self.search_results,
            key_findings=(f"Error: {error_message}",),
            synthesis="",
            confidence_score=0.0,
            processing_time_ms=self.processing_time_ms,
            created_at=self.created_at,
            completed_at=datetime.now(),
        )

    @property
    def source_count(self) -> int:
        """Get the number of sources consulted."""
        return len(self.search_results)

    @property
    def is_complete(self) -> bool:
        """Check if the research is complete."""
        return self.status == ResearchStatus.COMPLETED

    @property
    def is_successful(self) -> bool:
        """Check if the research was successful."""
        return self.is_complete and self.confidence_score > 0.3

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "query_id": str(self.query_id),
            "status": self.status.value,
            "search_results": [sr.to_dict() for sr in self.search_results],
            "key_findings": list(self.key_findings),
            "synthesis": self.synthesis,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "source_count": self.source_count,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
