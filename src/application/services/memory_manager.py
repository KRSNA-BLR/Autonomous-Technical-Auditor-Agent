"""
Memory Manager - Short-term memory management for the research agent.

This module provides conversation memory and context retrieval capabilities
to maintain coherent multi-turn research sessions.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryEntry:
    """A single entry in the agent's memory."""

    query: str
    response: str
    timestamp: datetime
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "response": self.response,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MemoryManager:
    """
    Short-term memory manager for the research agent.

    Maintains a sliding window of recent interactions to provide
    context for ongoing research sessions.
    """

    max_entries: int = 20
    _entries: deque[MemoryEntry] = field(default_factory=lambda: deque(maxlen=20))

    def __post_init__(self) -> None:
        """Initialize the memory with correct max length."""
        self._entries = deque(maxlen=self.max_entries)

    def add_interaction(
        self,
        query: str,
        response: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a new interaction to memory.

        Args:
            query: The user's query
            response: The agent's response
            metadata: Optional metadata about the interaction
        """
        entry = MemoryEntry(
            query=query,
            response=response,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self._entries.append(entry)

    def get_recent_context(self, n: int = 5) -> list[MemoryEntry]:
        """
        Get the N most recent interactions.

        Args:
            n: Number of recent entries to retrieve

        Returns:
            List of recent memory entries
        """
        entries = list(self._entries)
        return entries[-n:] if len(entries) >= n else entries

    def get_relevant_context(
        self,
        query: str,
        max_entries: int = 3,
    ) -> str:
        """
        Get context relevant to the current query.

        Uses simple keyword matching to find relevant past interactions.
        In a production system, this could use embeddings for semantic search.

        Args:
            query: The current query to find context for
            max_entries: Maximum number of entries to return

        Returns:
            Formatted string of relevant context
        """
        if not self._entries:
            return ""

        query_words = set(query.lower().split())
        scored_entries: list[tuple[float, MemoryEntry]] = []

        for entry in self._entries:
            entry_words = set(entry.query.lower().split())
            # Calculate simple overlap score
            overlap = len(query_words & entry_words)
            if overlap > 0:
                score = overlap / max(len(query_words), len(entry_words))
                scored_entries.append((score, entry))

        # Sort by score descending
        scored_entries.sort(key=lambda x: x[0], reverse=True)

        # Format relevant entries
        relevant = scored_entries[:max_entries]
        if not relevant:
            return ""

        context_parts = []
        for score, entry in relevant:
            context_parts.append(
                f"Previous Query: {entry.query}\n"
                f"Previous Finding: {entry.response[:500]}..."
            )

        return "\n\n".join(context_parts)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the current memory state."""
        return {
            "total_entries": len(self._entries),
            "max_entries": self.max_entries,
            "oldest_entry": (
                self._entries[0].timestamp.isoformat() if self._entries else None
            ),
            "newest_entry": (
                self._entries[-1].timestamp.isoformat() if self._entries else None
            ),
        }

    def clear(self) -> None:
        """Clear all memory entries."""
        self._entries.clear()

    def to_list(self) -> list[dict[str, Any]]:
        """Convert all entries to a list of dictionaries."""
        return [entry.to_dict() for entry in self._entries]

    def __len__(self) -> int:
        """Return the number of entries in memory."""
        return len(self._entries)

    def __bool__(self) -> bool:
        """Return True if memory has entries."""
        return bool(self._entries)
