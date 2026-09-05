"""Editable trading configuration.

Changing these values changes selection behaviour; it does not grant permission
for live financial execution. Live execution must still pass the core approval gate.
"""

from dataclasses import dataclass, field


@dataclass
class TradingConfig:
    # User-adjustable maximum number of simultaneous candidate/live positions.
    max_positions: int = 4

    # Minimum composite confidence required before a setup is presented.
    min_confidence: float = 0.70

    # Maximum risk budget per position, expressed as a fraction of account equity.
    max_risk_per_trade: float = 0.01

    # Maximum total risk budget across the four positions.
    max_total_risk: float = 0.04

    # Indicator periods can be changed without changing the engine.
    periods: dict[str, int] = field(default_factory=lambda: {
        "sma_fast": 20,
        "sma_slow": 50,
        "ema_fast": 12,
        "ema_slow": 26,
        "rsi": 14,
        "atr": 14,
        "bollinger": 20,
    })

    # Financial actions remain approval-required by design.
    require_explicit_approval: bool = True

    def validate(self) -> None:
        if not 1 <= self.max_positions <= 4:
            raise ValueError("max_positions must be between 1 and 4")
        if not 0 < self.min_confidence <= 1:
            raise ValueError("min_confidence must be in (0, 1]")
        if not 0 < self.max_risk_per_trade <= 1:
            raise ValueError("max_risk_per_trade must be in (0, 1]")
        if not 0 < self.max_total_risk <= 1:
            raise ValueError("max_total_risk must be in (0, 1]")
        if self.max_positions * self.max_risk_per_trade > self.max_total_risk:
            raise ValueError("position risk can exceed total risk budget")
