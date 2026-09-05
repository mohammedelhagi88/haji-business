"""Command routing for Haji Business."""

from dataclasses import dataclass
from typing import Callable

from .models import RiskLevel, Task
from .permissions import PermissionGate


@dataclass
class Command:
    name: str
    handler: Callable[[str], object]
    risk: RiskLevel = RiskLevel.SAFE


class CommandEngine:
    def __init__(self, permissions: PermissionGate | None = None) -> None:
        self.permissions = permissions or PermissionGate()
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        self._commands[command.name.lower()] = command

    def execute(self, name: str, payload: str = "") -> object:
        command = self._commands.get(name.lower())
        if command is None:
            raise KeyError(f"Unknown command: {name}")
        if not self.permissions.check(command.risk):
            return self.permissions.request_approval(
                action=command.name,
                risk=command.risk,
                reason="This command requires explicit user approval.",
            )
        return command.handler(payload)


def create_task_handler(payload: str) -> Task:
    return Task(title=payload.strip() or "Untitled task")
