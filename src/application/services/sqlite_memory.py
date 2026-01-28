"""
SQLite Memory Manager - Persistent memory storage for the research agent.

This module provides persistent conversation memory using SQLite,
ensuring research history is preserved between sessions.

Author: Danilo Viteri
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MemoryEntry:
    """A single entry in the agent's memory."""

    id: int | None
    query: str
    response: str
    timestamp: datetime
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "query": self.query,
            "response": self.response,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class SQLiteMemoryManager:
    """
    Persistent memory manager using SQLite.

    Stores all research interactions in a local SQLite database,
    enabling memory persistence across application restarts.
    """

    def __init__(
        self,
        db_path: str = "./data/memory.db",
        max_entries: int = 100,
    ) -> None:
        """
        Initialize the SQLite memory manager.

        Args:
            db_path: Path to the SQLite database file
            max_entries: Maximum entries to keep (older ones are pruned)
        """
        self.db_path = Path(db_path)
        self.max_entries = max_entries
        self._ensure_db_exists()
        logger.info(
            "SQLiteMemoryManager initialized",
            db_path=str(self.db_path),
            max_entries=max_entries,
        )

    def _ensure_db_exists(self) -> None:
        """Create database and tables if they don't exist."""
        # Create directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON memory_entries(timestamp DESC)
            """)
            conn.commit()

    def add_interaction(
        self,
        query: str,
        response: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a new interaction to persistent memory.

        Args:
            query: The user's query
            response: The agent's response
            metadata: Optional metadata about the interaction
        """
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memory_entries (query, response, timestamp, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (query, response, timestamp, metadata_json),
            )
            conn.commit()

            # Prune old entries if exceeding max
            cursor.execute("SELECT COUNT(*) FROM memory_entries")
            count = cursor.fetchone()[0]

            if count > self.max_entries:
                excess = count - self.max_entries
                cursor.execute(
                    """
                    DELETE FROM memory_entries
                    WHERE id IN (
                        SELECT id FROM memory_entries
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                    """,
                    (excess,),
                )
                conn.commit()
                logger.debug("Pruned old memory entries", removed=excess)

        logger.debug("Added interaction to memory", query=query[:50])

    def get_recent_context(self, n: int = 5) -> list[MemoryEntry]:
        """
        Get the N most recent interactions.

        Args:
            n: Number of recent entries to retrieve

        Returns:
            List of recent memory entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, query, response, timestamp, metadata
                FROM memory_entries
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (n,),
            )
            rows = cursor.fetchall()

        entries = []
        for row in reversed(rows):  # Reverse to get chronological order
            entries.append(
                MemoryEntry(
                    id=row[0],
                    query=row[1],
                    response=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    metadata=json.loads(row[4]) if row[4] else {},
                )
            )
        return entries

    def get_relevant_context(
        self,
        query: str,
        max_entries: int = 3,
    ) -> str:
        """
        Get context relevant to the current query.

        Uses keyword matching to find relevant past interactions.

        Args:
            query: The current query to find context for
            max_entries: Maximum number of entries to return

        Returns:
            Formatted string of relevant context
        """
        # Get recent entries to search through
        recent = self.get_recent_context(n=20)

        if not recent:
            return ""

        query_words = set(query.lower().split())
        scored_entries: list[tuple[float, MemoryEntry]] = []

        for entry in recent:
            entry_words = set(entry.query.lower().split())
            overlap = len(query_words & entry_words)
            if overlap > 0:
                score = overlap / max(len(query_words), len(entry_words))
                scored_entries.append((score, entry))

        scored_entries.sort(key=lambda x: x[0], reverse=True)
        relevant = scored_entries[:max_entries]

        if not relevant:
            return ""

        context_parts = []
        for _score, entry in relevant:
            context_parts.append(
                f"Previous Query: {entry.query}\nPrevious Finding: {entry.response[:500]}..."
            )

        return "\n\n".join(context_parts)

    def search_memory(self, keyword: str, limit: int = 10) -> list[MemoryEntry]:
        """
        Search memory entries by keyword.

        Args:
            keyword: Keyword to search for
            limit: Maximum results to return

        Returns:
            List of matching memory entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, query, response, timestamp, metadata
                FROM memory_entries
                WHERE query LIKE ? OR response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"%{keyword}%", f"%{keyword}%", limit),
            )
            rows = cursor.fetchall()

        return [
            MemoryEntry(
                id=row[0],
                query=row[1],
                response=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                metadata=json.loads(row[4]) if row[4] else {},
            )
            for row in rows
        ]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the current memory state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM memory_entries")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT timestamp FROM memory_entries ORDER BY timestamp ASC LIMIT 1")
            oldest = cursor.fetchone()

            cursor.execute("SELECT timestamp FROM memory_entries ORDER BY timestamp DESC LIMIT 1")
            newest = cursor.fetchone()

        return {
            "total_entries": total,
            "max_entries": self.max_entries,
            "oldest_entry": oldest[0] if oldest else None,
            "newest_entry": newest[0] if newest else None,
            "db_path": str(self.db_path),
            "db_size_kb": round(self.db_path.stat().st_size / 1024, 2)
            if self.db_path.exists()
            else 0,
        }

    def clear(self) -> None:
        """Clear all memory entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory_entries")
            conn.commit()
        logger.info("Memory cleared")

    def to_list(self) -> list[dict[str, Any]]:
        """Convert all entries to a list of dictionaries."""
        entries = self.get_recent_context(n=self.max_entries)
        return [entry.to_dict() for entry in entries]

    def __len__(self) -> int:
        """Return the number of entries in memory."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_entries")
            result = cursor.fetchone()
            return int(result[0]) if result else 0

    def __bool__(self) -> bool:
        """Return True if memory has entries."""
        return len(self) > 0


# Alias for backward compatibility
MemoryManager = SQLiteMemoryManager
