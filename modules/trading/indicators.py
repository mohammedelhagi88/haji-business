"""Technical indicator primitives for the trading module.

Pure functions keep indicators testable and independent from any broker.
Input series are expected in chronological order (oldest -> newest).
"""

from math import sqrt


def sma(values: list[float], period: int) -> list[float]:
    if period <= 0 or len(values) < period:
        return []
    return [sum(values[i-period+1:i+1]) / period for i in range(period-1, len(values))]


def ema(values: list[float], period: int) -> list[float]:
    if period <= 0 or len(values) < period:
        return []
    alpha = 2 / (period + 1)
    result = [sum(values[:period]) / period]
    for value in values[period:]:
        result.append((value * alpha) + (result[-1] * (1 - alpha)))
    return result


def wma(values: list[float], period: int) -> list[float]:
    if period <= 0 or len(values) < period:
        return []
    weights = range(1, period + 1)
    denominator = period * (period + 1) / 2
    return [sum(v*w for v, w in zip(values[i-period+1:i+1], weights)) / denominator
            for i in range(period-1, len(values))]


def rsi(values: list[float], period: int = 14) -> list[float]:
    if period <= 0 or len(values) <= period:
        return []
    gains, losses = [], []
    for previous, current in zip(values, values[1:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result = [_rsi_value(avg_gain, avg_loss)]
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        result.append(_rsi_value(avg_gain, avg_loss))
    return result


def _rsi_value(gain: float, loss: float) -> float:
    if loss == 0:
        return 100.0 if gain > 0 else 50.0
    return 100 - (100 / (1 + gain / loss))


def bollinger_bands(values: list[float], period: int = 20, deviations: float = 2.0) -> list[tuple[float, float, float]]:
    if period <= 0 or len(values) < period:
        return []
    bands = []
    for i in range(period - 1, len(values)):
        window = values[i-period+1:i+1]
        mean = sum(window) / period
        variance = sum((v - mean) ** 2 for v in window) / period
        std = sqrt(variance)
        bands.append((mean - deviations * std, mean, mean + deviations * std))
    return bands


def true_range(high: list[float], low: list[float], close: list[float]) -> list[float]:
    if not (len(high) == len(low) == len(close)) or not close:
        return []
    result = [high[0] - low[0]]
    for h, l, previous_close in zip(high[1:], low[1:], close[:-1]):
        result.append(max(h - l, abs(h - previous_close), abs(l - previous_close)))
    return result


def atr(high: list[float], low: list[float], close: list[float], period: int = 14) -> list[float]:
    return sma(true_range(high, low, close), period)


def obv(close: list[float], volume: list[float]) -> list[float]:
    if len(close) != len(volume) or not close:
        return []
    total = 0.0
    result = [total]
    for previous, current, vol in zip(close, close[1:], volume[1:]):
        if current > previous:
            total += vol
        elif current < previous:
            total -= vol
        result.append(total)
    return result


def vwap(high: list[float], low: list[float], close: list[float], volume: list[float]) -> float | None:
    if not (len(high) == len(low) == len(close) == len(volume)) or not close:
        return None
    total_volume = sum(volume)
    if total_volume == 0:
        return None
    return sum(((h + l + c) / 3) * v for h, l, c, v in zip(high, low, close, volume)) / total_volume
