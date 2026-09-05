"""Market-data contracts and safety validation for trading analysis."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, Sequence


@dataclass(frozen=True)
class MarketBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def validate(self) -> None:
        values = (self.open, self.high, self.low, self.close, self.volume)
        if any(value != value or value in (float("inf"), float("-inf")) for value in values):
            raise ValueError("bar_contains_non_finite_value")
        if self.volume < 0:
            raise ValueError("bar_volume_negative")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("bar_high_invalid")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("bar_low_invalid")


@dataclass(frozen=True)
class MarketSnapshotRequest:
    symbol: str
    limit: int = 200
    max_age_seconds: int = 300


class MarketDataProvider(Protocol):
    def snapshot(self, request: MarketSnapshotRequest) -> Sequence[MarketBar]:
        """Return bars ordered oldest -> newest."""


def validate_bars(
    bars: Sequence[MarketBar], *, now: datetime | None = None, max_age_seconds: int = 300
) -> list[MarketBar]:
    if not bars:
        raise ValueError("market_data_empty")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds_invalid")
    for bar in bars:
        bar.validate()
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("market_data_not_strictly_ordered")
    reference = now or datetime.now(timezone.utc)
    latest = bars[-1].timestamp
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    age = (reference - latest.astimezone(timezone.utc)).total_seconds()
    if age < -5:
        raise ValueError("market_data_timestamp_in_future")
    if age > max_age_seconds:
        raise ValueError("market_data_stale")
    return list(bars)
