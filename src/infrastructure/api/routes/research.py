"""
Research Routes - API endpoints for research operations.

This module defines the REST API endpoints for conducting research,
retrieving results, and managing the research agent.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.services.memory_manager import MemoryManager
from src.application.services.research_agent import ResearchAgentService
from src.domain.entities.query import QueryPriority, QueryType, ResearchQuery
from src.domain.entities.report import ReportFormat
from src.infrastructure.api.dependencies import (
    get_memory_manager,
    get_research_agent,
)
from src.infrastructure.api.schemas.research import (
    HealthResponse,
    MemoryResponse,
    ResearchReportResponse,
    ResearchRequest,
    ResearchResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/research",
    response_model=ResearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Conduct autonomous research",
    description=(
        "Submit a research query and receive comprehensive findings. "
        "The agent will search the web, analyze content, and synthesize results."
    ),
)
async def conduct_research(
    request: ResearchRequest,
    agent: Annotated[ResearchAgentService, Depends(get_research_agent)],
) -> ResearchResponse:
    """
    Conduct autonomous research on a given topic.

    Args:
        request: Research request with query details
        agent: Injected research agent service

    Returns:
        ResearchResponse with findings and synthesis
    """
    logger.info(
        "Research request received",
        question=request.question[:100],
        query_type=request.query_type,
    )

    try:
        # Create domain query entity
        query = ResearchQuery.create(
            question=request.question,
            context=request.context or "",
            query_type=QueryType(request.query_type),
            priority=QueryPriority(request.priority),
            max_sources=request.max_sources,
            keywords=tuple(request.keywords) if request.keywords else None,
        )

        # Execute research
        result = await agent.research(query)

        # Check for failure
        if not result.is_complete:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Research failed to complete",
            )

        logger.info(
            "Research completed",
            query_id=str(query.id),
            confidence=result.confidence_score,
        )

        return ResearchResponse(
            query_id=str(result.query_id),
            status=result.status.value,
            synthesis=result.synthesis,
            key_findings=list(result.key_findings),
            sources=[
                {
                    "title": sr.title,
                    "url": sr.url,
                    "snippet": sr.snippet,
                }
                for sr in result.search_results
            ],
            confidence_score=result.confidence_score,
            processing_time_ms=result.processing_time_ms,
        )

    except ValueError as e:
        logger.error("Invalid research request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Research failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research failed: {str(e)}",
        )


@router.post(
    "/research/report",
    response_model=ResearchReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a detailed research report",
    description=(
        "Conduct research and generate a formatted report with "
        "executive summary, sections, and recommendations."
    ),
)
async def generate_research_report(
    request: ResearchRequest,
    agent: Annotated[ResearchAgentService, Depends(get_research_agent)],
) -> ResearchReportResponse:
    """
    Generate a comprehensive research report.

    Args:
        request: Research request
        agent: Research agent service

    Returns:
        Detailed research report
    """
    logger.info("Report generation requested", question=request.question[:100])

    try:
        # Create query
        query = ResearchQuery.create(
            question=request.question,
            context=request.context or "",
            query_type=QueryType(request.query_type),
            priority=QueryPriority(request.priority),
            max_sources=request.max_sources,
        )

        # Execute research
        result = await agent.research(query)

        # Generate report
        report = await agent.generate_report(
            research=result,
            query=query,
            report_format=ReportFormat.JSON,
        )

        return ResearchReportResponse(
            report_id=str(report.id),
            title=report.title,
            executive_summary=report.executive_summary,
            sections=[
                {
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "sources": list(s.sources),
                }
                for s in report.get_sections_sorted()
            ],
            recommendations=list(report.recommendations),
            confidence_level=report.confidence_level,
            metadata=report.metadata,
        )

    except Exception as e:
        logger.error("Report generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.get(
    "/memory",
    response_model=MemoryResponse,
    summary="Get agent memory state",
    description="Retrieve the current state of the agent's short-term memory.",
)
async def get_memory_state(
    memory: Annotated[MemoryManager, Depends(get_memory_manager)],
) -> MemoryResponse:
    """
    Get the current memory state.

    Args:
        memory: Memory manager instance

    Returns:
        Memory state summary
    """
    summary = memory.get_summary()
    entries = memory.to_list()

    return MemoryResponse(
        total_entries=summary["total_entries"],
        max_entries=summary["max_entries"],
        oldest_entry=summary["oldest_entry"],
        newest_entry=summary["newest_entry"],
        entries=entries,
    )


@router.delete(
    "/memory",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear agent memory",
    description="Clear all entries from the agent's short-term memory.",
)
async def clear_memory(
    memory: Annotated[MemoryManager, Depends(get_memory_manager)],
) -> None:
    """
    Clear all memory entries.

    Args:
        memory: Memory manager instance
    """
    memory.clear()
    logger.info("Memory cleared")


@router.get(
    "/status",
    response_model=HealthResponse,
    summary="Get agent status",
    description="Get detailed status of the research agent and its components.",
)
async def get_agent_status(
    agent: Annotated[ResearchAgentService, Depends(get_research_agent)],
    memory: Annotated[MemoryManager, Depends(get_memory_manager)],
) -> HealthResponse:
    """
    Get detailed agent status.

    Args:
        agent: Research agent
        memory: Memory manager

    Returns:
        Detailed health status
    """
    return HealthResponse(
        status="healthy",
        components={
            "agent": {
                "tools": [t.name for t in agent.tools],
                "status": "ready",
            },
            "memory": memory.get_summary(),
        },
    )
