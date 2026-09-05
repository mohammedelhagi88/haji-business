"""Public Binance Spot market-data adapter.

This adapter reads public klines only. It never authenticates, transfers funds,
or places orders.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .market_data import MarketBar, MarketDataProvider, MarketSnapshotRequest


class BinancePublicMarketData(MarketDataProvider):
    def __init__(self, base_url: str = "https://api.binance.com", timeout: float = 8.0, interval: str = "1m"):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.interval = interval

    def snapshot(self, request: MarketSnapshotRequest) -> list[MarketBar]:
        if not request.symbol.strip():
            raise ValueError("symbol_required")
        if not 20 <= request.limit <= 1000:
            raise ValueError("limit_out_of_range")
        query = urlencode({"symbol": request.symbol.replace("/", "").upper(), "interval": self.interval, "limit": request.limit})
        req = Request(f"{self.base_url}/api/v3/klines?{query}", headers={"Accept": "application/json"})
        with urlopen(req, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("invalid_market_response")
        bars: list[MarketBar] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 6:
                raise ValueError("invalid_kline")
            bars.append(MarketBar(
                timestamp=datetime.fromtimestamp(float(row[0]) / 1000, tz=timezone.utc),
                open=float(row[1]), high=float(row[2]), low=float(row[3]),
                close=float(row[4]), volume=float(row[5]),
            ))
        return bars
