"""Task lifecycle management."""

from .models import Task


class TaskManager:
    def __init__(self) -> None:
        self._tasks: list[Task] = []

    def add(self, task: Task) -> Task:
        self._tasks.append(task)
        return task

    def complete(self, task: Task) -> Task:
        task.status = "completed"
        return task

    def list(self, status: str | None = None) -> list[Task]:
        if status is None:
            return list(self._tasks)
        return [task for task in self._tasks if task.status == status]
