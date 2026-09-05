import pytest

from modules.trading.broker import PaperBroker
from modules.trading.approval import ApprovedTrade, TradingApprovalBridge
from modules.trading.selector import TradeCandidate


def candidate():
    return TradeCandidate("BTCUSDT", "BUY", 100, 98, 104, .8, .8, .01, ("test",))


def test_paper_broker_requires_approval():
    bridge = TradingApprovalBridge()
    request = bridge.request(candidate())
    trade = ApprovedTrade(candidate(), request)
    with pytest.raises(PermissionError):
        PaperBroker().execute(trade)


def test_paper_broker_executes_only_simulation():
    bridge = TradingApprovalBridge()
    request = bridge.approve(bridge.request(candidate()))
    result = PaperBroker().execute(ApprovedTrade(candidate(), request))
    assert result.status == "paper_executed"
