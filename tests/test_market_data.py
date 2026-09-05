from datetime import datetime, timedelta, timezone

import pytest

from modules.trading.market_data import MarketBar, validate_bars


def bars(age=0):
    now = datetime.now(timezone.utc) - timedelta(seconds=age)
    return [
        MarketBar(now - timedelta(minutes=2), 99, 101, 98, 100, 10),
        MarketBar(now - timedelta(minutes=1), 100, 102, 99, 101, 12),
        MarketBar(now, 101, 103, 100, 102, 14),
    ]


def test_validates_ordered_fresh_bars():
    assert len(validate_bars(bars(), max_age_seconds=60)) == 3


def test_rejects_stale_data():
    with pytest.raises(ValueError, match="market_data_stale"):
        validate_bars(bars(120), max_age_seconds=60)


def test_rejects_invalid_ohlc():
    invalid = bars()
    invalid[-1] = MarketBar(invalid[-1].timestamp, 101, 99, 100, 102, 14)
    with pytest.raises(ValueError, match="bar_high_invalid"):
        validate_bars(invalid)
