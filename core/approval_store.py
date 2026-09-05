"""Persistent, expiring approval records for sensitive agent actions."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any


class PersistentApprovalStore:
    """SQLite store for approvals that must survive an API restart.

    Records are one-time consumable and may expire. Payload is application-
    specific JSON (for example, a serialized trade candidate).
    """

    def __init__(self, path: str = "haji_memory.sqlite3", ttl_seconds: int = 900) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds_must_be_positive")
        self.ttl_seconds = ttl_seconds
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                risk TEXT NOT NULL,
                reason TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0
            )"""
        )
        self._db.commit()

    def put(self, approval_id: str, action: str, risk: str, reason: str, payload: Any) -> None:
        now = datetime.utcnow()
        self._db.execute(
            "INSERT OR REPLACE INTO approvals(approval_id,action,risk,reason,payload,created_at,consumed) VALUES(?,?,?,?,?,?,0)",
            (approval_id, action, risk, reason, json.dumps(payload, ensure_ascii=False, default=str), now.isoformat()),
        )
        self._db.commit()

    def consume(self, approval_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT action,risk,reason,payload,created_at,consumed FROM approvals WHERE approval_id=?",
            (approval_id,),
        ).fetchone()
        if row is None or row[5]:
            return None
        try:
            created = datetime.fromisoformat(row[4])
        except (TypeError, ValueError):
            return None
        if datetime.utcnow() - created > timedelta(seconds=self.ttl_seconds):
            return None
        self._db.execute("UPDATE approvals SET consumed=1 WHERE approval_id=? AND consumed=0", (approval_id,))
        if self._db.total_changes <= 0:
            return None
        self._db.commit()
        return {
            "action": row[0], "risk": row[1], "reason": row[2],
            "payload": json.loads(row[3]), "created_at": row[4],
        }

    def close(self) -> None:
        self._db.close()
