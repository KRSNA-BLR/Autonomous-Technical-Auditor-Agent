# =============================================================================
# Dockerfile - Multi-Stage Optimized Build
# =============================================================================
# This Dockerfile uses multi-stage builds to create a minimal, secure image
# following Docker best practices for production deployments.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build the application
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files
WORKDIR /app
COPY pyproject.toml ./

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -e . && \
    pip install uvicorn[standard]

# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Labels for container metadata
LABEL maintainer="Your Name <your.email@example.com>" \
    version="1.0.0" \
    description="Autonomous Tech Research Agent - AI-powered research automation" \
    org.opencontainers.image.source="https://github.com/yourusername/autonomous-tech-research-agent"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Application settings
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    LOG_LEVEL=INFO

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup pyproject.toml ./

# Install the application
RUN pip install -e . --no-deps

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 3: Development - With dev dependencies
# -----------------------------------------------------------------------------
FROM production as development

# Switch to root to install dev dependencies
USER root

# Install development dependencies
RUN pip install -e ".[dev]"

# Switch back to non-root user
USER appuser

# Override command for development with auto-reload
CMD ["uvicorn", "src.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
