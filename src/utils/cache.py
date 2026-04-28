from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional


class ResponseCache:
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
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get(self, cache_key: str) -> Optional[Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM response_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, cache_key: str, payload: Any) -> None:
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO response_cache (cache_key, payload)
                    VALUES (?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload
                    """,
                    (cache_key, json.dumps(payload)),
                )
                connection.commit()
