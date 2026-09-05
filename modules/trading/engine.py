"""Trading analysis pipeline: indicators -> signal -> ranked candidates."""

from dataclasses import dataclass

from .config import TradingConfig
from .indicators import atr
from .selector import TradeCandidate, TradeSelector, build_levels
from .signals import composite_signal


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    close: list[float]
    high: list[float]
    low: list[float]
    volume: list[float]


class TradingEngine:
    """Analyze snapshots and return up to N candidates; never submits orders."""

    def __init__(self, config: TradingConfig | None = None):
        self.config = config or TradingConfig()
        self.selector = TradeSelector(self.config)

    def analyze(self, snapshot: MarketSnapshot) -> TradeCandidate | None:
        p = self.config.periods
        signal = composite_signal(
            snapshot.close,
            snapshot.volume,
            snapshot.high,
            snapshot.low,
            sma_fast_period=p["sma_fast"],
            sma_slow_period=p["sma_slow"],
            ema_fast_period=p["ema_fast"],
            ema_slow_period=p["ema_slow"],
            rsi_period=p["rsi"],
            bollinger_period=p["bollinger"],
        )
        if signal.direction == 0 or signal.confidence < self.config.min_confidence:
            return None

        atr_values = atr(
            snapshot.high, snapshot.low, snapshot.close, p["atr"]
        )
        if not atr_values:
            return None
        entry = snapshot.close[-1]
        stop, target = build_levels(
            "BUY" if signal.direction > 0 else "SELL",
            entry,
            atr_values[-1],
        )
        return TradeCandidate(
            symbol=snapshot.symbol,
            side="BUY" if signal.direction > 0 else "SELL",
            entry=entry,
            stop_loss=stop,
            take_profit=target,
            confidence=signal.confidence,
            score=abs(signal.score),
            risk_fraction=self.config.max_risk_per_trade,
            reasons=signal.reasons,
        )

    def rank(self, snapshots: list[MarketSnapshot]) -> list[TradeCandidate]:
        candidates = [c for s in snapshots if (c := self.analyze(s)) is not None]
        return self.selector.select(candidates)
