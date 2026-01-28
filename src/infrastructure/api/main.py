"""
FastAPI Application - Main API entry point.

This module configures and runs the FastAPI application with all routes,
middleware, and exception handlers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infrastructure.api.routes import research
from src.infrastructure.api.dependencies import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info("🚀 Starting Autonomous Tech Research Agent")
    settings = get_settings()
    logger.info(
        "Configuration loaded",
        model=settings.llm_model,
        debug=settings.api_debug,
    )

    yield

    # Shutdown
    logger.info("👋 Shutting down Autonomous Tech Research Agent")


def create_app() -> FastAPI:
    """
    Application factory function.

    Creates and configures the FastAPI application instance.

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    app = FastAPI(
        title="Autonomous Tech Research Agent",
        description=(
            "🔬 An autonomous AI agent that conducts technical research "
            "using web search and text analysis. Built with Clean Architecture, "
            "FastAPI, and LangChain."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.api_debug else "An error occurred",
            },
        )

    # Include routers
    app.include_router(research.router, prefix="/api/v1", tags=["Research"])

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "research-agent"}

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": "Autonomous Tech Research Agent",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.infrastructure.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
