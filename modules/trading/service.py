"""Trading orchestration: data -> analysis -> explicit approval requests."""
from dataclasses import dataclass

from .approval import TradingApprovalBridge
from .config import TradingConfig
from .engine import MarketSnapshot, TradingEngine
from .market_data import MarketBar, MarketDataProvider, MarketSnapshotRequest, validate_bars
from .selector import TradeCandidate


@dataclass(frozen=True)
class TradeOpportunity:
    candidate: TradeCandidate
    approval: object


class TradingService:
    """Analyze provider data and prepare, but never execute, financial orders."""

    def __init__(self, provider: MarketDataProvider, config: TradingConfig | None = None,
                 approvals: TradingApprovalBridge | None = None):
        self.provider = provider
        self.engine = TradingEngine(config)
        self.approvals = approvals or TradingApprovalBridge()

    @staticmethod
    def _snapshot(symbol: str, bars: list[MarketBar]) -> MarketSnapshot:
        return MarketSnapshot(
            symbol=symbol,
            close=[b.close for b in bars],
            high=[b.high for b in bars],
            low=[b.low for b in bars],
            volume=[b.volume for b in bars],
        )

    def analyze(self, symbols: list[str], *, limit: int = 200, max_age_seconds: int = 300) -> list[TradeOpportunity]:
        candidates: list[TradeCandidate] = []
        for symbol in symbols:
            request = MarketSnapshotRequest(symbol=symbol, limit=limit, max_age_seconds=max_age_seconds)
            bars = validate_bars(self.provider.snapshot(request), max_age_seconds=max_age_seconds)
            candidate = self.engine.analyze(self._snapshot(symbol, bars))
            if candidate is not None:
                candidates.append(candidate)
        selected = self.engine.selector.select(candidates)
        return [TradeOpportunity(candidate=c, approval=self.approvals.request(c)) for c in selected]
