"""
Report Entity - Represents the final research report.

This entity structures the final output that will be delivered to the user,
with proper formatting and organization of findings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID, uuid4

from src.domain.entities.research import ResearchResult


class ReportFormat(str, Enum):
    """Available report formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"


@dataclass(frozen=True, slots=True)
class ReportSection:
    """
    Immutable entity representing a section of the report.

    Attributes:
        title: Section title
        content: Section content
        order: Display order
        sources: References for this section
    """

    title: str
    content: str
    order: int
    sources: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate the section."""
        if not self.title:
            raise ValueError("Section title cannot be empty")
        if self.order < 0:
            raise ValueError("Order must be non-negative")

    @classmethod
    def create(
        cls,
        title: str,
        content: str,
        order: int,
        sources: tuple[str, ...] | None = None,
    ) -> Self:
        """Factory method to create a ReportSection."""
        return cls(
            title=title.strip(),
            content=content.strip(),
            order=order,
            sources=sources or tuple(),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "order": self.order,
            "sources": list(self.sources),
        }


@dataclass(frozen=True, slots=True)
class ResearchReport:
    """
    Immutable entity representing the final research report.

    Attributes:
        id: Unique identifier
        research_id: Reference to the research result
        title: Report title
        executive_summary: Brief summary of findings
        sections: Report sections with detailed content
        recommendations: Actionable recommendations
        confidence_level: Overall confidence in the report
        format: Report format
        metadata: Additional metadata
        created_at: When the report was created
    """

    id: UUID
    research_id: UUID
    title: str
    executive_summary: str
    sections: tuple[ReportSection, ...]
    recommendations: tuple[str, ...]
    confidence_level: str
    format: ReportFormat
    metadata: dict[str, str | int | float]
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate the report."""
        if not self.title:
            raise ValueError("Report title cannot be empty")
        if not self.executive_summary:
            raise ValueError("Executive summary cannot be empty")

    @classmethod
    def from_research(
        cls,
        research: ResearchResult,
        title: str,
        sections: tuple[ReportSection, ...],
        recommendations: tuple[str, ...],
        report_format: ReportFormat = ReportFormat.JSON,
    ) -> Self:
        """
        Factory method to create a report from research results.

        Args:
            research: The research result to base the report on
            title: Report title
            sections: Report sections
            recommendations: Actionable recommendations
            report_format: Desired output format

        Returns:
            A new ResearchReport instance
        """
        confidence_level = cls._calculate_confidence_level(research.confidence_score)

        executive_summary = research.synthesis or "No synthesis available."

        metadata: dict[str, str | int | float] = {
            "sources_consulted": research.source_count,
            "findings_count": len(research.key_findings),
            "processing_time_ms": research.processing_time_ms,
            "confidence_score": research.confidence_score,
        }

        return cls(
            id=uuid4(),
            research_id=research.id,
            title=title,
            executive_summary=executive_summary,
            sections=sections,
            recommendations=recommendations,
            confidence_level=confidence_level,
            format=report_format,
            metadata=metadata,
            created_at=datetime.now(),
        )

    @staticmethod
    def _calculate_confidence_level(score: float) -> str:
        """Calculate human-readable confidence level."""
        if score >= 0.8:
            return "High - Results are well-supported by multiple sources"
        elif score >= 0.6:
            return "Medium - Results are reasonably supported"
        elif score >= 0.4:
            return "Low - Results should be verified"
        else:
            return "Very Low - Insufficient evidence"

    @property
    def section_count(self) -> int:
        """Get the number of sections."""
        return len(self.sections)

    def get_sections_sorted(self) -> list[ReportSection]:
        """Get sections sorted by order."""
        return sorted(self.sections, key=lambda s: s.order)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "research_id": str(self.research_id),
            "title": self.title,
            "executive_summary": self.executive_summary,
            "sections": [s.to_dict() for s in self.get_sections_sorted()],
            "recommendations": list(self.recommendations),
            "confidence_level": self.confidence_level,
            "format": self.format.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def to_markdown(self) -> str:
        """Convert to Markdown format."""
        lines = [
            f"# {self.title}",
            "",
            "## Executive Summary",
            "",
            self.executive_summary,
            "",
        ]

        for section in self.get_sections_sorted():
            lines.extend([
                f"## {section.title}",
                "",
                section.content,
                "",
            ])
            if section.sources:
                lines.append("**Sources:**")
                for source in section.sources:
                    lines.append(f"- {source}")
                lines.append("")

        if self.recommendations:
            lines.extend([
                "## Recommendations",
                "",
            ])
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        lines.extend([
            "---",
            f"*Confidence Level: {self.confidence_level}*",
            f"*Generated at: {self.created_at.isoformat()}*",
        ])

        return "\n".join(lines)
