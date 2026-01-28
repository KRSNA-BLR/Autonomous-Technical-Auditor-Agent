"""
Research Schemas - Pydantic v2 models for API request/response validation.

This module defines the data transfer objects (DTOs) for the research API,
providing strong typing and automatic validation.
"""

from typing import Any

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """
    Request schema for conducting research.

    Attributes:
        question: The research question to investigate
        context: Additional context to guide the research
        query_type: Type of research (technical, comparative, exploratory, deep_dive)
        priority: Priority level (low, medium, high, critical)
        max_sources: Maximum number of sources to consult
        keywords: Optional keywords to focus the search
    """

    question: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="The research question to investigate",
        examples=["What are the best practices for FastAPI in production?"],
    )
    context: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context to guide the research",
        examples=["Focus on performance optimization and security"],
    )
    query_type: str = Field(
        default="technical",
        description="Type of research to conduct",
        examples=["technical", "comparative", "exploratory", "deep_dive"],
    )
    priority: str = Field(
        default="medium",
        description="Priority level of the research",
        examples=["low", "medium", "high", "critical"],
    )
    max_sources: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of sources to consult",
    )
    keywords: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Keywords to focus the search",
        examples=[["FastAPI", "performance", "security"]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What are the best practices for FastAPI in production?",
                    "context": "Focus on performance and security best practices",
                    "query_type": "technical",
                    "priority": "high",
                    "max_sources": 5,
                    "keywords": ["FastAPI", "production", "performance"],
                }
            ]
        }
    }


class SourceInfo(BaseModel):
    """Information about a research source."""

    title: str = Field(..., description="Title of the source")
    url: str = Field(..., description="URL of the source")
    snippet: str = Field(..., description="Relevant snippet from the source")


class ResearchResponse(BaseModel):
    """
    Response schema for research results.

    Attributes:
        query_id: Unique identifier for the research query
        status: Status of the research (completed, failed, partial)
        synthesis: Synthesized analysis of all findings
        key_findings: List of key findings extracted
        sources: List of sources consulted
        confidence_score: Confidence in the research quality (0-1)
        processing_time_ms: Time taken to process in milliseconds
    """

    query_id: str = Field(..., description="Unique identifier for this research")
    status: str = Field(..., description="Research status")
    synthesis: str = Field(..., description="Synthesized analysis of findings")
    key_findings: list[str] = Field(
        default_factory=list,
        description="Key findings extracted from research",
    )
    sources: list[dict[str, str]] = Field(
        default_factory=list,
        description="Sources consulted during research",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the research quality",
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "completed",
                    "synthesis": "FastAPI production best practices include...",
                    "key_findings": [
                        "Use Gunicorn with Uvicorn workers",
                        "Implement proper error handling",
                        "Enable CORS with specific origins",
                    ],
                    "sources": [
                        {
                            "title": "FastAPI Documentation",
                            "url": "https://fastapi.tiangolo.com/",
                            "snippet": "FastAPI is a modern, fast...",
                        }
                    ],
                    "confidence_score": 0.85,
                    "processing_time_ms": 3500,
                }
            ]
        }
    }


class ReportSection(BaseModel):
    """A section of the research report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    order: int = Field(..., description="Display order")
    sources: list[str] = Field(
        default_factory=list,
        description="Sources referenced in this section",
    )


class ResearchReportResponse(BaseModel):
    """
    Response schema for a complete research report.

    Attributes:
        report_id: Unique identifier for the report
        title: Report title
        executive_summary: Brief summary of findings
        sections: Detailed report sections
        recommendations: Actionable recommendations
        confidence_level: Human-readable confidence assessment
        metadata: Additional report metadata
    """

    report_id: str = Field(..., description="Unique report identifier")
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(..., description="Executive summary")
    sections: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Report sections",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations",
    )
    confidence_level: str = Field(..., description="Confidence level assessment")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Report metadata",
    )


class MemoryEntry(BaseModel):
    """A single memory entry."""

    query: str = Field(..., description="The query that was asked")
    response: str = Field(..., description="The response that was given")
    timestamp: str = Field(..., description="When the interaction occurred")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class MemoryResponse(BaseModel):
    """Response schema for memory state."""

    total_entries: int = Field(..., description="Total number of entries in memory")
    max_entries: int = Field(..., description="Maximum entries allowed")
    oldest_entry: str | None = Field(None, description="Timestamp of oldest entry")
    newest_entry: str | None = Field(None, description="Timestamp of newest entry")
    entries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Memory entries",
    )


class HealthResponse(BaseModel):
    """Response schema for health/status checks."""

    status: str = Field(..., description="Overall status")
    components: dict[str, Any] = Field(
        default_factory=dict,
        description="Status of individual components",
    )
