from modules.trading.config import TradingConfig
from modules.trading.selector import TradeCandidate, TradeSelector, build_levels


def test_selects_at_most_four_and_respects_confidence():
    config = TradingConfig(max_positions=4, min_confidence=0.70)
    selector = TradeSelector(config)
    candidates = [
        TradeCandidate(f"ASSET{i}", "BUY", 100, 99, 102, confidence, score, 0.01)
        for i, (confidence, score) in enumerate(
            [(0.95, 0.95), (0.90, 0.90), (0.85, 0.85), (0.80, 0.80), (0.60, 0.99)]
        )
    ]
    selected = selector.select(candidates)
    assert len(selected) == 4
    assert all(c.confidence >= 0.70 for c in selected)


def test_selector_does_not_force_four_when_only_two_are_valid():
    selector = TradeSelector(TradingConfig(max_positions=4, min_confidence=0.70))
    candidates = [
        TradeCandidate("A", "BUY", 100, 99, 102, 0.90, 0.90, 0.01),
        TradeCandidate("B", "SELL", 100, 101, 98, 0.80, 0.80, 0.01),
        TradeCandidate("C", "BUY", 100, 99, 102, 0.50, 0.99, 0.01),
    ]
    assert [c.symbol for c in selector.select(candidates)] == ["A", "B"]


def test_build_levels_for_buy_and_sell():
    assert build_levels("BUY", 100, 2.0) == (97.0, 106.0)
    assert build_levels("SELL", 100, 2.0) == (103.0, 94.0)
