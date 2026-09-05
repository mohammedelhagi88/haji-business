"""Execution boundary for trading.

Only the paper broker is implemented. A live broker must be a separate adapter and
must receive a concrete, current approval before any order submission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .approval import ApprovedTrade


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    symbol: str
    side: str
    detail: str


class Broker(Protocol):
    def execute(self, trade: ApprovedTrade) -> ExecutionResult: ...


class PaperBroker:
    """Safe simulator: records no external order and moves no money."""

    def execute(self, trade: ApprovedTrade) -> ExecutionResult:
        if not trade.approval.approved:
            raise PermissionError("explicit_current_approval_required")
        c = trade.candidate
        return ExecutionResult(
            status="paper_executed",
            symbol=c.symbol,
            side=c.side,
            detail=f"محاكاة فقط: entry={c.entry} stop={c.stop_loss} target={c.take_profit}",
        )
