"""
Unit tests for application services.

These tests verify the business logic in the application layer,
including the memory manager and agent configuration.
"""

import gc
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.application.services.sqlite_memory import MemoryEntry, SQLiteMemoryManager


@pytest.fixture
def temp_db_path() -> str:
    """Create a temporary database path for each test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Force garbage collection to release SQLite connections on Windows
    gc.collect()
    time.sleep(0.1)
    # Cleanup after test
    for _ in range(3):
        try:
            if Path(path).exists():
                Path(path).unlink()
            break
        except PermissionError:
            gc.collect()
            time.sleep(0.2)


class TestMemoryManager:
    """Tests for SQLiteMemoryManager service."""

    def test_create_memory_manager(self, temp_db_path: str) -> None:
        """Test creating a memory manager."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        assert len(memory) == 0
        assert memory.max_entries == 10

    def test_add_interaction(self, temp_db_path: str) -> None:
        """Test adding an interaction to memory."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)
        memory.add_interaction(
            query="What is FastAPI?",
            response="FastAPI is a modern web framework...",
            metadata={"source": "test"},
        )

        assert len(memory) == 1
        entries = memory.get_recent_context(1)
        assert entries[0].query == "What is FastAPI?"
        assert entries[0].response == "FastAPI is a modern web framework..."

    def test_memory_limit(self, temp_db_path: str) -> None:
        """Test that memory respects max_entries limit."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=3)

        for i in range(5):
            memory.add_interaction(
                query=f"Query {i}",
                response=f"Response {i}",
            )

        assert len(memory) == 3
        entries = memory.get_recent_context(10)
        # Should have queries 2, 3, 4 (oldest ones evicted)
        queries = [e.query for e in entries]
        assert "Query 0" not in queries
        assert "Query 1" not in queries
        assert "Query 4" in queries

    def test_get_recent_context(self, temp_db_path: str) -> None:
        """Test getting recent context."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        for i in range(5):
            memory.add_interaction(
                query=f"Query {i}",
                response=f"Response {i}",
            )

        recent = memory.get_recent_context(3)
        assert len(recent) == 3
        assert recent[-1].query == "Query 4"

    def test_get_relevant_context(self, temp_db_path: str) -> None:
        """Test getting relevant context based on query."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        memory.add_interaction(
            query="How to deploy FastAPI?",
            response="Use uvicorn or gunicorn...",
        )
        memory.add_interaction(
            query="What is React?",
            response="React is a JavaScript library...",
        )
        memory.add_interaction(
            query="FastAPI performance tips",
            response="Use async endpoints...",
        )

        context = memory.get_relevant_context("FastAPI deployment guide")

        assert "FastAPI" in context
        assert "deploy" in context.lower() or "performance" in context.lower()

    def test_get_relevant_context_no_matches(self, temp_db_path: str) -> None:
        """Test getting relevant context with no matches."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        memory.add_interaction(
            query="Python basics",
            response="Python is a programming language...",
        )

        context = memory.get_relevant_context("Kubernetes deployment")
        # Should return empty string if no relevant matches
        assert context == "" or "Python" not in context

    def test_memory_summary(self, temp_db_path: str) -> None:
        """Test getting memory summary."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        memory.add_interaction(query="Test 1", response="Response 1")
        memory.add_interaction(query="Test 2", response="Response 2")

        summary = memory.get_summary()

        assert summary["total_entries"] == 2
        assert summary["max_entries"] == 10
        assert summary["oldest_entry"] is not None
        assert summary["newest_entry"] is not None

    def test_clear_memory(self, temp_db_path: str) -> None:
        """Test clearing memory."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        memory.add_interaction(query="Test", response="Response")
        assert len(memory) == 1

        memory.clear()
        assert len(memory) == 0

    def test_memory_to_list(self, temp_db_path: str) -> None:
        """Test converting memory to list."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        memory.add_interaction(
            query="Test query",
            response="Test response",
            metadata={"key": "value"},
        )

        entries = memory.to_list()

        assert len(entries) == 1
        assert entries[0]["query"] == "Test query"
        assert entries[0]["response"] == "Test response"
        assert entries[0]["metadata"]["key"] == "value"

    def test_memory_bool(self, temp_db_path: str) -> None:
        """Test memory truthiness."""
        memory = SQLiteMemoryManager(db_path=temp_db_path, max_entries=10)

        assert not memory
        memory.add_interaction(query="Test", response="Response")
        assert memory


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_memory_entry_creation(self) -> None:
        """Test creating a memory entry."""
        entry = MemoryEntry(
            id=None,
            query="What is Python?",
            response="Python is a programming language.",
            timestamp=datetime.now(),
            metadata={"source": "test"},
        )

        assert entry.query == "What is Python?"
        assert entry.response == "Python is a programming language."
        assert entry.metadata["source"] == "test"

    def test_memory_entry_to_dict(self) -> None:
        """Test serializing memory entry to dict."""
        now = datetime.now()
        entry = MemoryEntry(
            id=1,
            query="Test",
            response="Response",
            timestamp=now,
            metadata={},
        )

        data = entry.to_dict()

        assert data["query"] == "Test"
        assert data["response"] == "Response"
        assert data["timestamp"] == now.isoformat()
        assert data["id"] == 1
