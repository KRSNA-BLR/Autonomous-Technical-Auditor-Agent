"""
Unit tests for domain entities.

These tests verify the business logic in the domain layer,
ensuring entities behave correctly and maintain invariants.
"""

import pytest
from datetime import datetime
from uuid import UUID

from src.domain.entities.query import (
    ResearchQuery,
    QueryType,
    QueryPriority,
)
from src.domain.entities.research import (
    ResearchResult,
    SearchResult,
    ResearchStatus,
    SourceCredibility,
)
from src.domain.entities.report import (
    ResearchReport,
    ReportSection,
    ReportFormat,
)


class TestResearchQuery:
    """Tests for ResearchQuery entity."""

    def test_create_valid_query(self) -> None:
        """Test creating a valid research query."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
            context="Focus on production deployment",
            query_type=QueryType.TECHNICAL,
            priority=QueryPriority.HIGH,
            max_sources=5,
        )

        assert isinstance(query.id, UUID)
        assert query.question == "What are the best practices for FastAPI?"
        assert query.context == "Focus on production deployment"
        assert query.query_type == QueryType.TECHNICAL
        assert query.priority == QueryPriority.HIGH
        assert query.max_sources == 5
        assert isinstance(query.created_at, datetime)

    def test_query_with_keywords(self) -> None:
        """Test creating query with keywords."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
            keywords=("FastAPI", "Python", "REST"),
        )

        assert query.keywords == ("FastAPI", "Python", "REST")
        assert "FastAPI" in query.search_query
        assert "Python" in query.search_query

    def test_query_immutable_update(self) -> None:
        """Test immutable keyword update."""
        original = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        updated = original.with_keywords(("new", "keywords"))

        assert original.keywords == ()
        assert updated.keywords == ("new", "keywords")
        assert original.id == updated.id

    def test_query_validation_short_question(self) -> None:
        """Test validation rejects short questions."""
        with pytest.raises(ValueError, match="at least 10 characters"):
            ResearchQuery.create(question="Short")

    def test_query_validation_max_sources_range(self) -> None:
        """Test validation of max_sources range."""
        with pytest.raises(ValueError, match="between 1 and 20"):
            ResearchQuery.create(
                question="Valid question that is long enough",
                max_sources=25,
            )

    def test_query_to_dict(self) -> None:
        """Test serialization to dictionary."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
            query_type=QueryType.TECHNICAL,
        )
        data = query.to_dict()

        assert "id" in data
        assert data["question"] == "What are the best practices for FastAPI?"
        assert data["query_type"] == "technical"


class TestSearchResult:
    """Tests for SearchResult entity."""

    def test_create_valid_search_result(self) -> None:
        """Test creating a valid search result."""
        result = SearchResult.create(
            title="FastAPI Documentation",
            url="https://fastapi.tiangolo.com/",
            snippet="FastAPI is a modern, fast web framework...",
            credibility=SourceCredibility.HIGH,
        )

        assert result.title == "FastAPI Documentation"
        assert result.url == "https://fastapi.tiangolo.com/"
        assert result.credibility == SourceCredibility.HIGH
        assert isinstance(result.retrieved_at, datetime)

    def test_search_result_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from inputs."""
        result = SearchResult.create(
            title="  FastAPI  ",
            url="  https://example.com  ",
            snippet="  Some text  ",
        )

        assert result.title == "FastAPI"
        assert result.url == "https://example.com"
        assert result.snippet == "Some text"

    def test_search_result_validation_empty_title(self) -> None:
        """Test validation rejects empty title."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            SearchResult.create(title="", url="https://example.com", snippet="text")

    def test_search_result_to_dict(self) -> None:
        """Test serialization to dictionary."""
        result = SearchResult.create(
            title="Test",
            url="https://example.com",
            snippet="Test snippet",
        )
        data = result.to_dict()

        assert data["title"] == "Test"
        assert data["url"] == "https://example.com"
        assert "retrieved_at" in data


class TestResearchResult:
    """Tests for ResearchResult entity."""

    def test_create_pending_result(self) -> None:
        """Test creating a pending research result."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        result = ResearchResult.create_pending(query.id)

        assert result.status == ResearchStatus.PENDING
        assert result.query_id == query.id
        assert result.confidence_score == 0.0
        assert result.search_results == ()
        assert result.key_findings == ()

    def test_result_with_findings(self) -> None:
        """Test completing a research result with findings."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        pending = ResearchResult.create_pending(query.id)

        search_results = (
            SearchResult.create(
                title="Test",
                url="https://example.com",
                snippet="Test snippet",
            ),
        )

        completed = pending.with_results(
            search_results=search_results,
            key_findings=("Finding 1", "Finding 2"),
            synthesis="This is the synthesis",
            confidence_score=0.8,
            processing_time_ms=1500,
        )

        assert completed.status == ResearchStatus.COMPLETED
        assert completed.is_complete
        assert completed.is_successful
        assert completed.source_count == 1
        assert len(completed.key_findings) == 2
        assert completed.confidence_score == 0.8
        assert completed.completed_at is not None

    def test_result_mark_failed(self) -> None:
        """Test marking a result as failed."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        pending = ResearchResult.create_pending(query.id)
        failed = pending.mark_failed("Connection timeout")

        assert failed.status == ResearchStatus.FAILED
        assert not failed.is_complete
        assert not failed.is_successful
        assert "Error: Connection timeout" in failed.key_findings

    def test_result_validation_confidence_range(self) -> None:
        """Test confidence score validation."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        pending = ResearchResult.create_pending(query.id)

        with pytest.raises(ValueError, match="between 0 and 1"):
            pending.with_results(
                search_results=(),
                key_findings=(),
                synthesis="",
                confidence_score=1.5,  # Invalid
                processing_time_ms=100,
            )


class TestReportSection:
    """Tests for ReportSection entity."""

    def test_create_valid_section(self) -> None:
        """Test creating a valid report section."""
        section = ReportSection.create(
            title="Key Findings",
            content="The main findings are...",
            order=1,
            sources=("https://example.com",),
        )

        assert section.title == "Key Findings"
        assert section.content == "The main findings are..."
        assert section.order == 1
        assert len(section.sources) == 1

    def test_section_validation_empty_title(self) -> None:
        """Test validation rejects empty title."""
        with pytest.raises(ValueError, match="title cannot be empty"):
            ReportSection.create(title="", content="Some content", order=0)


class TestResearchReport:
    """Tests for ResearchReport entity."""

    def test_create_report_from_research(self) -> None:
        """Test creating a report from research results."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        pending = ResearchResult.create_pending(query.id)
        research = pending.with_results(
            search_results=(),
            key_findings=("Finding 1",),
            synthesis="This is the synthesis of findings.",
            confidence_score=0.75,
            processing_time_ms=2000,
        )

        sections = (
            ReportSection.create(
                title="Overview",
                content="This section provides an overview.",
                order=1,
            ),
        )

        report = ResearchReport.from_research(
            research=research,
            title="FastAPI Best Practices Report",
            sections=sections,
            recommendations=("Recommendation 1", "Recommendation 2"),
        )

        assert "FastAPI Best Practices Report" in report.title
        assert report.section_count == 1
        assert len(report.recommendations) == 2
        assert "Medium" in report.confidence_level
        assert report.metadata["confidence_score"] == 0.75

    def test_report_to_markdown(self) -> None:
        """Test markdown generation."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        pending = ResearchResult.create_pending(query.id)
        research = pending.with_results(
            search_results=(),
            key_findings=(),
            synthesis="Synthesis text.",
            confidence_score=0.5,
            processing_time_ms=1000,
        )

        report = ResearchReport.from_research(
            research=research,
            title="Test Report",
            sections=(
                ReportSection.create(
                    title="Section 1",
                    content="Content here.",
                    order=1,
                ),
            ),
            recommendations=("Do this",),
            report_format=ReportFormat.MARKDOWN,
        )

        markdown = report.to_markdown()

        assert "# Test Report" in markdown
        assert "## Executive Summary" in markdown
        assert "## Section 1" in markdown
        assert "## Recommendations" in markdown
        assert "1. Do this" in markdown


class TestConfidenceLevel:
    """Tests for confidence level calculation."""

    @pytest.mark.parametrize(
        "score,expected_keyword",
        [
            (0.9, "High"),
            (0.7, "Medium"),
            (0.5, "Low"),
            (0.2, "Very Low"),
        ],
    )
    def test_confidence_level_calculation(
        self, score: float, expected_keyword: str
    ) -> None:
        """Test confidence level calculation for various scores."""
        query = ResearchQuery.create(
            question="What are the best practices for FastAPI?",
        )
        pending = ResearchResult.create_pending(query.id)
        research = pending.with_results(
            search_results=(),
            key_findings=(),
            synthesis="Test",
            confidence_score=score,
            processing_time_ms=100,
        )

        report = ResearchReport.from_research(
            research=research,
            title="Test",
            sections=(),
            recommendations=(),
        )

        assert expected_keyword in report.confidence_level
