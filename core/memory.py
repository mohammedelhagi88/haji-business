"""Simple in-memory context store; replaceable by a persistent backend later."""

from datetime import datetime
from typing import Any

from .models import MemoryItem


class MemoryStore:
    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def set(self, key: str, value: Any) -> MemoryItem:
        item = MemoryItem(key=key, value=value, updated_at=datetime.utcnow())
        self._items[key] = item
        return item

    def get(self, key: str, default: Any = None) -> Any:
        item = self._items.get(key)
        return default if item is None else item.value

    def delete(self, key: str) -> bool:
        return self._items.pop(key, None) is not None
