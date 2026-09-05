"""Permission and approval gate for Haji Business actions."""

from .models import ApprovalRequest, RiskLevel


class PermissionGate:
    """Blocks sensitive/financial actions until explicit approval."""

    def check(self, risk: RiskLevel) -> bool:
        return risk == RiskLevel.SAFE

    def request_approval(self, action: str, risk: RiskLevel, reason: str) -> ApprovalRequest:
        if risk == RiskLevel.SAFE:
            return ApprovalRequest(action=action, risk=risk, reason=reason, approved=True)
        return ApprovalRequest(action=action, risk=risk, reason=reason, approved=False)

    def approve(self, request: ApprovalRequest) -> ApprovalRequest:
        request.approved = True
        return request
