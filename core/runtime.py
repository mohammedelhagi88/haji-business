"""Continuous, event-driven runtime for Haji Business.

The runtime coordinates registered modules without busy-waiting. Modules are
called when an event arrives or when their scheduled interval is due.
Sensitive and financial actions remain behind the core permission gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable


Handler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class RuntimeEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ScheduledModule:
    name: str
    interval: timedelta
    handler: Handler
    next_run: datetime
    enabled: bool = True


class HajiRuntime:
    """Small orchestration loop suitable for API workers, CLIs, or a service."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self._scheduled: dict[str, ScheduledModule] = {}
        self.running = False

    def on(self, event_name: str, handler: Handler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def schedule(
        self,
        name: str,
        interval_seconds: float,
        handler: Handler,
        *,
        start_at: datetime | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        now = start_at or datetime.now(timezone.utc)
        self._scheduled[name] = ScheduledModule(
            name=name,
            interval=timedelta(seconds=interval_seconds),
            handler=handler,
            next_run=now,
        )

    def emit(self, event: RuntimeEvent) -> list[Any]:
        results: list[Any] = []
        for handler in self._handlers.get(event.name, []):
            results.append(handler(event.payload))
        return results

    def tick(self, now: datetime | None = None) -> list[Any]:
        """Run due scheduled modules once; the host controls tick frequency."""
        current = now or datetime.now(timezone.utc)
        results: list[Any] = []
        for module in self._scheduled.values():
            if not module.enabled or current < module.next_run:
                continue
            results.append(module.handler({"runtime_time": current.isoformat()}))
            module.next_run = current + module.interval
        return results

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "event_handlers": {name: len(items) for name, items in self._handlers.items()},
            "scheduled_modules": {
                name: {"enabled": item.enabled, "next_run": item.next_run.isoformat()}
                for name, item in self._scheduled.items()
            },
        }
