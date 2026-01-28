"""
Memory Manager - Memory management for the research agent.

This module provides the main memory interface, now backed by SQLite
for persistent storage across sessions.

Author: Danilo Viteri
"""

# Re-export from sqlite_memory for backward compatibility
from src.application.services.sqlite_memory import (
    MemoryEntry,
    MemoryManager,
    SQLiteMemoryManager,
)

__all__ = ["MemoryEntry", "MemoryManager", "SQLiteMemoryManager"]
