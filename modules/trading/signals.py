"""Composite technical-analysis signals.

The functions return analysis data only. They do not execute trades.
"""

from dataclasses import dataclass

from .indicators import bollinger_bands, ema, obv, rsi, sma, vwap


@dataclass(frozen=True)
class SignalResult:
    direction: int  # 1 = bullish, -1 = bearish, 0 = neutral
    score: float
    confidence: float
    reasons: tuple[str, ...]


def composite_signal(
    close: list[float],
    volume: list[float],
    high: list[float],
    low: list[float],
    *,
    sma_fast_period: int = 20,
    sma_slow_period: int = 50,
    ema_fast_period: int = 12,
    ema_slow_period: int = 26,
    rsi_period: int = 14,
    bollinger_period: int = 20,
) -> SignalResult:
    """Combine trend, momentum, volatility, and volume into one editable score."""
    if not close or len(close) != len(volume) or len(close) != len(high) or len(close) != len(low):
        raise ValueError("OHLCV series must be non-empty and have equal lengths")

    reasons: list[str] = []
    votes: list[float] = []

    sf = sma(close, sma_fast_period)
    ss = sma(close, sma_slow_period)
    if sf and ss:
        if sf[-1] > ss[-1]:
            votes.append(1.0); reasons.append("SMA trend bullish")
        elif sf[-1] < ss[-1]:
            votes.append(-1.0); reasons.append("SMA trend bearish")

    ef = ema(close, ema_fast_period)
    es = ema(close, ema_slow_period)
    if ef and es:
        if ef[-1] > es[-1]:
            votes.append(1.0); reasons.append("EMA trend bullish")
        elif ef[-1] < es[-1]:
            votes.append(-1.0); reasons.append("EMA trend bearish")

    rv = rsi(close, rsi_period)
    if rv:
        if rv[-1] < 30:
            votes.append(1.0); reasons.append("RSI oversold")
        elif rv[-1] > 70:
            votes.append(-1.0); reasons.append("RSI overbought")
        elif rv[-1] >= 50:
            votes.append(0.5); reasons.append("RSI above 50")
        else:
            votes.append(-0.5); reasons.append("RSI below 50")

    bands = bollinger_bands(close, bollinger_period)
    if bands:
        lower, _, upper = bands
        if close[-1] <= lower[-1]:
            votes.append(1.0); reasons.append("Price at/below lower Bollinger band")
        elif close[-1] >= upper[-1]:
            votes.append(-1.0); reasons.append("Price at/above upper Bollinger band")

    ov = obv(close, volume)
    if len(ov) >= 2:
        if ov[-1] > ov[-2]:
            votes.append(0.5); reasons.append("OBV rising")
        elif ov[-1] < ov[-2]:
            votes.append(-0.5); reasons.append("OBV falling")

    vw = vwap(high, low, close, volume)
    if vw:
        if close[-1] > vw[-1]:
            votes.append(0.5); reasons.append("Price above VWAP")
        elif close[-1] < vw[-1]:
            votes.append(-0.5); reasons.append("Price below VWAP")

    if not votes:
        return SignalResult(0, 0.0, 0.0, tuple(reasons))

    score = sum(votes) / len(votes)
    confidence = min(1.0, abs(score))
    direction = 1 if score > 0 else -1 if score < 0 else 0
    return SignalResult(direction, score, confidence, tuple(reasons))
