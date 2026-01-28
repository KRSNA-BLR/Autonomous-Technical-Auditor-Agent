"""
Integration tests for the API endpoints.

These tests verify that the API endpoints work correctly
with mocked dependencies.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "research-agent"

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Autonomous Tech Research Agent"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestDocsEndpoints:
    """Tests for documentation endpoints."""

    def test_openapi_schema(self, client: TestClient) -> None:
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_docs_endpoint(self, client: TestClient) -> None:
        """Test Swagger docs endpoint."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client: TestClient) -> None:
        """Test ReDoc endpoint."""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestResearchEndpoints:
    """Tests for research endpoints."""

    def test_research_request_validation(self, client: TestClient) -> None:
        """Test request validation for research endpoint."""
        # Missing required field
        response = client.post("/api/v1/research", json={})

        assert response.status_code == 422

        # Question too short
        response = client.post(
            "/api/v1/research",
            json={"question": "Short"},
        )

        assert response.status_code == 422

    def test_research_requires_api_key(self, client: TestClient) -> None:
        """Test that research endpoint requires API key configuration."""
        # Without GROQ_API_KEY set, should fail
        with patch.dict("os.environ", {}, clear=True):
            response = client.post(
                "/api/v1/research",
                json={
                    "question": "What are the best practices for FastAPI in production?",
                    "query_type": "technical",
                    "max_sources": 5,
                },
            )

            # Should fail due to missing API key
            assert response.status_code in [500, 422]


class TestMemoryEndpoints:
    """Tests for memory management endpoints."""

    def test_get_memory_state(self, client: TestClient) -> None:
        """Test getting memory state."""
        response = client.get("/api/v1/memory")

        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert "max_entries" in data

    def test_clear_memory(self, client: TestClient) -> None:
        """Test clearing memory."""
        response = client.delete("/api/v1/memory")

        assert response.status_code == 204


class TestRequestSchemas:
    """Tests for request schema validation."""

    def test_valid_research_request_schema(self, client: TestClient) -> None:
        """Test that valid request schemas are accepted."""
        # Note: This will fail without API key, but validates schema
        valid_request = {
            "question": "What are the best practices for FastAPI in production deployments?",
            "context": "Focus on security and performance",
            "query_type": "technical",
            "priority": "high",
            "max_sources": 5,
            "keywords": ["FastAPI", "production", "security"],
        }

        response = client.post("/api/v1/research", json=valid_request)

        # Schema should be valid (even if request fails for other reasons)
        assert response.status_code != 422

    def test_invalid_query_type(self, client: TestClient) -> None:
        """Test that invalid query type is handled."""
        invalid_request = {
            "question": "What are the best practices for FastAPI?",
            "query_type": "invalid_type",
        }

        response = client.post("/api/v1/research", json=invalid_request)

        # Should either reject with 422 or handle gracefully
        assert response.status_code in [400, 422, 500]

    def test_max_sources_limits(self, client: TestClient) -> None:
        """Test max_sources validation limits."""
        # Too many sources
        response = client.post(
            "/api/v1/research",
            json={
                "question": "What are the best practices for FastAPI?",
                "max_sources": 100,
            },
        )

        assert response.status_code == 422

        # Negative sources
        response = client.post(
            "/api/v1/research",
            json={
                "question": "What are the best practices for FastAPI?",
                "max_sources": -1,
            },
        )

        assert response.status_code == 422
