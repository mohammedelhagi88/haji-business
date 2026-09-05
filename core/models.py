"""Core domain models for Haji Business.

The models are intentionally small so modules can build on stable primitives.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    SAFE = "safe"
    SENSITIVE = "sensitive"
    FINANCIAL = "financial"


@dataclass
class Task:
    title: str
    description: str = ""
    risk: RiskLevel = RiskLevel.SAFE
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    action: str
    risk: RiskLevel
    reason: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved: bool = False


@dataclass
class MemoryItem:
    key: str
    value: Any
    updated_at: datetime = field(default_factory=datetime.utcnow)
