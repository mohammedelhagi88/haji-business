"""Notification routing for runtime events and task lifecycle updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .runtime import HajiRuntime, RuntimeEvent


@dataclass(frozen=True)
class Notification:
    title: str
    message: str
    level: str = "info"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


NotificationHandler = Callable[[Notification], Any]


class NotificationService:
    """In-process notification hub with runtime-event routing.

    Adapters can later deliver push/SMS/Telegram/etc. without changing the
    core event or task APIs. Delivery itself is always explicit at adapter level.
    """

    def __init__(self, runtime: HajiRuntime | None = None) -> None:
        self._handlers: list[NotificationHandler] = []
        self._history: list[Notification] = []
        if runtime is not None:
            self.attach(runtime)

    def register(self, handler: NotificationHandler) -> None:
        self._handlers.append(handler)

    def notify(self, notification: Notification) -> list[Any]:
        self._history.append(notification)
        return [handler(notification) for handler in self._handlers]

    def emit(self, title: str, message: str, *, level: str = "info", metadata: dict[str, Any] | None = None) -> list[Any]:
        return self.notify(Notification(title, message, level, metadata=metadata or {}))

    def history(self) -> list[Notification]:
        return list(self._history)

    def attach(self, runtime: HajiRuntime) -> None:
        runtime.on("agent.message", lambda payload: self.emit("حاجي", str(payload.get("message", "")), metadata=payload))
        runtime.on("approval.granted", lambda payload: self.emit("تمت الموافقة", "تم تسجيل الموافقة على الإجراء.", metadata=payload))
        runtime.on("trading.paper_executed", lambda payload: self.emit("تداول تجريبي", f"تم تنفيذ صفقة تجريبية على {payload.get('symbol', 'غير معروف')}.", metadata=payload))
        runtime.on("task.created", lambda payload: self.emit("مهمة جديدة", str(payload.get("title", "تمت إضافة مهمة.")), metadata=payload))
        runtime.on("task.completed", lambda payload: self.emit("مهمة مكتملة", str(payload.get("title", "اكتملت مهمة.")), metadata=payload))
