"""Trading approval bridge.

Turns ranked trade candidates into explicit financial approval requests.
This module does not place orders; execution must be handled by a broker
adapter only after a current approval is granted.
"""

from dataclasses import dataclass

from core.models import ApprovalRequest, RiskLevel
from core.permissions import PermissionGate

from .selector import TradeCandidate


@dataclass(frozen=True)
class ApprovedTrade:
    candidate: TradeCandidate
    approval: ApprovalRequest


class TradingApprovalBridge:
    """Create and validate explicit approvals for selected trade candidates."""

    def __init__(self, gate: PermissionGate | None = None):
        self.gate = gate or PermissionGate()

    def request(self, candidate: TradeCandidate) -> ApprovalRequest:
        action = (
            f"trade {candidate.side} {candidate.symbol} "
            f"entry={candidate.entry} stop={candidate.stop_loss} "
            f"target={candidate.take_profit} risk={candidate.risk_fraction}"
        )
        reason = (
            f"confidence={candidate.confidence:.2f}; score={candidate.score:.2f}; "
            f"reward_risk={candidate.reward_risk:.2f}; "
            f"reasons={'; '.join(candidate.reasons)}"
        )
        return self.gate.request_approval(action, RiskLevel.FINANCIAL, reason)

    def approve(self, request: ApprovalRequest) -> ApprovalRequest:
        if request.risk != RiskLevel.FINANCIAL:
            raise ValueError("Trading approvals must be financial-risk requests")
        return self.gate.approve(request)

    def approved_trade(
        self, candidate: TradeCandidate, request: ApprovalRequest
    ) -> ApprovedTrade:
        if not request.approved:
            raise PermissionError("Current explicit approval is required before execution")
        return ApprovedTrade(candidate=candidate, approval=request)
