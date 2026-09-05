"""SQLite-backed persistent memory for Haji AI."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from .models import MemoryItem


class PersistentMemoryStore:
    """Drop-in memory store that survives API restarts."""

    def __init__(self, path: str = "haji_memory.sqlite3") -> None:
        self.path = path
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        self._db.commit()

    def set(self, key: str, value: Any) -> MemoryItem:
        item = MemoryItem(key=key, value=value, updated_at=datetime.utcnow())
        encoded = json.dumps(value, ensure_ascii=False, default=str)
        self._db.execute(
            "INSERT INTO memory(key,value,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, encoded, item.updated_at.isoformat()),
        )
        self._db.commit()
        return item

    def get(self, key: str, default: Any = None) -> Any:
        row = self._db.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except (TypeError, ValueError):
            return row[0]

    def delete(self, key: str) -> bool:
        cursor = self._db.execute("DELETE FROM memory WHERE key=?", (key,))
        self._db.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._db.close()
