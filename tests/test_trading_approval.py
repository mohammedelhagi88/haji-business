import pytest

from core.models import RiskLevel
from core.permissions import PermissionGate
from modules.trading.approval import TradingApprovalBridge
from modules.trading.selector import TradeCandidate


def candidate():
    return TradeCandidate(
        symbol="BTC/USDT",
        side="BUY",
        entry=100.0,
        stop_loss=98.0,
        take_profit=104.0,
        confidence=0.80,
        score=0.80,
        risk_fraction=0.01,
        reasons=("trend aligned",),
    )


def test_request_requires_financial_approval():
    request = TradingApprovalBridge().request(candidate())
    assert request.risk == RiskLevel.FINANCIAL
    assert request.approved is False


def test_approved_trade_requires_current_approval():
    bridge = TradingApprovalBridge(PermissionGate())
    request = bridge.request(candidate())
    with pytest.raises(PermissionError):
        bridge.approved_trade(candidate(), request)

    approved = bridge.approve(request)
    result = bridge.approved_trade(candidate(), approved)
    assert result.candidate.symbol == "BTC/USDT"
    assert result.approval.approved is True
