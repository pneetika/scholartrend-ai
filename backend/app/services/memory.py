from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.common import MemoryEntry


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS research_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    executive_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def remember(self, session_id: str, role: str, content: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO memories (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                    (session_id, role, content, timestamp),
                )
                connection.commit()

    def recent(self, session_id: str, limit: int = 8) -> list[MemoryEntry]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT role, content, created_at
                FROM memories
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = cursor.fetchall()

        return [
            MemoryEntry(
                role=row[0],
                content=row[1],
                created_at=datetime.fromisoformat(row[2]),
            )
            for row in reversed(rows)
        ]

    def store_run(self, run_id: str, session_id: str, query: str, executive_summary: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO research_runs (run_id, session_id, query, executive_summary, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (run_id, session_id, query, executive_summary, timestamp),
                )
                connection.commit()

    def recent_runs(self, limit: int = 10) -> list[dict[str, str]]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT run_id, session_id, query, executive_summary, created_at
                FROM research_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        return [
            {
                "run_id": row[0],
                "session_id": row[1],
                "query": row[2],
                "executive_summary": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]

