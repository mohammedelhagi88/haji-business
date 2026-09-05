"""Mobile-friendly notification bridge.

The core emits normalized notification payloads; the mobile app can poll the
API for pending items until a push provider is configured.
"""
from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any


class MobileNotificationInbox:
    """Small in-process inbox used by the API/mobile integration."""

    def __init__(self, max_items: int = 100) -> None:
        if max_items <= 0:
            raise ValueError("max_items_must_be_positive")
        self._items: deque[dict[str, Any]] = deque(maxlen=max_items)
        self._lock = Lock()

    def push(self, payload: dict[str, Any]) -> dict[str, Any]:
        item = dict(payload)
        with self._lock:
            self._items.append(item)
        return item

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
