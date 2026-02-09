"""
Query Entity - Represents a research query from the user.

This entity encapsulates all the information needed to conduct a research task,
following the principle of making invalid states unrepresentable.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class QueryType(StrEnum):
    """Types of research queries the agent can handle."""

    TECHNICAL = "technical"
    COMPARATIVE = "comparative"
    EXPLORATORY = "exploratory"
    DEEP_DIVE = "deep_dive"


class QueryPriority(StrEnum):
    """Priority levels for research queries."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ResearchQuery:
    """
    Immutable entity representing a research query.

    Attributes:
        id: Unique identifier for the query
        question: The main research question
        context: Additional context to guide the research
        query_type: Type of research to conduct
        priority: Priority level of the query
        max_sources: Maximum number of sources to consult
        created_at: Timestamp when the query was created

    Example:
        >>> query = ResearchQuery.create(
        ...     question="What are the best practices for FastAPI in production?",
        ...     context="Focus on performance and security",
        ...     query_type=QueryType.TECHNICAL
        ... )
    """

    id: UUID
    question: str
    context: str
    query_type: QueryType
    priority: QueryPriority
    max_sources: int
    created_at: datetime
    keywords: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate the entity after initialization."""
        if not self.question or len(self.question.strip()) < 10:
            raise ValueError("Question must be at least 10 characters long")
        if self.max_sources < 1 or self.max_sources > 20:
            raise ValueError("max_sources must be between 1 and 20")

    @classmethod
    def create(
        cls,
        question: str,
        context: str = "",
        query_type: QueryType = QueryType.TECHNICAL,
        priority: QueryPriority = QueryPriority.MEDIUM,
        max_sources: int = 5,
        keywords: tuple[str, ...] | None = None,
    ) -> "ResearchQuery":
        """
        Factory method to create a new ResearchQuery.

        Args:
            question: The main research question
            context: Additional context (optional)
            query_type: Type of research
            priority: Priority level
            max_sources: Max sources to consult
            keywords: Keywords for search optimization

        Returns:
            A new ResearchQuery instance
        """
        return cls(
            id=uuid4(),
            question=question.strip(),
            context=context.strip(),
            query_type=query_type,
            priority=priority,
            max_sources=max_sources,
            created_at=datetime.now(),
            keywords=keywords or (),
        )

    def with_keywords(self, keywords: tuple[str, ...]) -> "ResearchQuery":
        """Create a new query with updated keywords (immutable update)."""
        return ResearchQuery(
            id=self.id,
            question=self.question,
            context=self.context,
            query_type=self.query_type,
            priority=self.priority,
            max_sources=self.max_sources,
            created_at=self.created_at,
            keywords=keywords,
        )

    @property
    def search_query(self) -> str:
        """Generate an optimized search query string."""
        parts = [self.question]
        if self.keywords:
            parts.extend(self.keywords)
        return " ".join(parts)

    def to_dict(self) -> dict[str, str | int | list[str]]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "question": self.question,
            "context": self.context,
            "query_type": self.query_type.value,
            "priority": self.priority.value,
            "max_sources": self.max_sources,
            "created_at": self.created_at.isoformat(),
            "keywords": list(self.keywords),
        }
