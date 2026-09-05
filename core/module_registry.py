"""Central registry for Haji AI modules.

Modules register capabilities here so the agent/runtime can discover the
same services from one place without hard-coding every feature into HajiAgent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    description: str
    handler: Callable[..., Any] | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleSpec] = {}

    def register(self, spec: ModuleSpec) -> ModuleSpec:
        key = spec.name.strip().lower()
        if not key:
            raise ValueError("module_name_required")
        if key in self._modules:
            raise ValueError("module_already_registered")
        self._modules[key] = spec
        return spec

    def upsert(self, spec: ModuleSpec) -> ModuleSpec:
        key = spec.name.strip().lower()
        if not key:
            raise ValueError("module_name_required")
        self._modules[key] = spec
        return spec

    def get(self, name: str) -> ModuleSpec | None:
        return self._modules.get(name.strip().lower())

    def list(self, *, enabled_only: bool = False) -> list[ModuleSpec]:
        values = list(self._modules.values())
        return [m for m in values if m.enabled] if enabled_only else values

    def capabilities(self) -> list[dict[str, Any]]:
        return [
            {"name": m.name, "description": m.description, "enabled": m.enabled}
            for m in self.list()
        ]

    def dispatch(self, name: str, *args: Any, **kwargs: Any) -> Any:
        module = self.get(name)
        if module is None or not module.enabled:
            raise KeyError("module_not_available")
        if module.handler is None:
            raise RuntimeError("module_handler_not_configured")
        return module.handler(*args, **kwargs)
