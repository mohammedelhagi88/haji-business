"""Editable trade candidate scoring and selection.

This module only analyzes/selects candidates. It never places a live order.
"""

from dataclasses import dataclass, field
from typing import Literal

from .config import TradingConfig

Side = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class TradeCandidate:
    symbol: str
    side: Side
    entry: float
    stop_loss: float
    take_profit: float
    confidence: float
    score: float
    risk_fraction: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def reward_risk(self) -> float:
        risk = abs(self.entry - self.stop_loss)
        reward = abs(self.take_profit - self.entry)
        return reward / risk if risk else 0.0


class TradeSelector:
    """Select up to the configured number of strongest valid setups."""

    def __init__(self, config: TradingConfig | None = None):
        self.config = config or TradingConfig()
        self.config.validate()

    def select(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
        valid = [c for c in candidates if self._valid(c)]
        valid.sort(key=lambda c: (c.score, c.confidence), reverse=True)

        selected: list[TradeCandidate] = []
        total_risk = 0.0
        for candidate in valid:
            if len(selected) >= self.config.max_positions:
                break
            if total_risk + candidate.risk_fraction > self.config.max_total_risk:
                continue
            selected.append(candidate)
            total_risk += candidate.risk_fraction
        return selected

    def _valid(self, candidate: TradeCandidate) -> bool:
        if not candidate.symbol.strip():
            return False
        if candidate.entry <= 0 or candidate.stop_loss <= 0 or candidate.take_profit <= 0:
            return False
        if candidate.confidence < self.config.min_confidence:
            return False
        if not 0 < candidate.risk_fraction <= self.config.max_risk_per_trade:
            return False
        if candidate.side == "BUY" and not (
            candidate.stop_loss < candidate.entry < candidate.take_profit
        ):
            return False
        if candidate.side == "SELL" and not (
            candidate.take_profit < candidate.entry < candidate.stop_loss
        ):
            return False
        return True


def build_levels(
    side: Side,
    entry: float,
    atr_value: float,
    atr_stop_multiplier: float = 1.5,
    risk_reward_ratio: float = 2.0,
) -> tuple[float, float]:
    """Build ATR-based stop and target levels for analysis."""
    if entry <= 0 or atr_value <= 0:
        raise ValueError("entry and atr_value must be positive")
    if atr_stop_multiplier <= 0 or risk_reward_ratio <= 0:
        raise ValueError("multipliers must be positive")

    distance = atr_value * atr_stop_multiplier
    reward = distance * risk_reward_ratio
    if side == "BUY":
        return entry - distance, entry + reward
    return entry + distance, entry - reward
