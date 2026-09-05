"""Task lifecycle management with optional runtime event integration."""

from __future__ import annotations

from .models import Task
from .runtime import HajiRuntime, RuntimeEvent


class TaskManager:
    def __init__(self, runtime: HajiRuntime | None = None) -> None:
        self._tasks: list[Task] = []
        self.runtime = runtime

    def add(self, task: Task) -> Task:
        self._tasks.append(task)
        if self.runtime is not None:
            self.runtime.emit(RuntimeEvent("task.created", {"title": task.title, "status": task.status}))
        return task

    def complete(self, task: Task) -> Task:
        task.status = "completed"
        if self.runtime is not None:
            self.runtime.emit(RuntimeEvent("task.completed", {"title": task.title, "status": task.status}))
        return task

    def list(self, status: str | None = None) -> list[Task]:
        if status is None:
            return list(self._tasks)
        return [task for task in self._tasks if task.status == status]
