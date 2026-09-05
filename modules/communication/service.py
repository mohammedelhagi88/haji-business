"""Safe communication orchestration layer.

Provider adapters are intentionally not bundled here. The service validates and
queues an intent, while a future phone/SMS/social adapter performs the real action.
"""

from dataclasses import dataclass
from typing import Callable, Dict

from .models import CommunicationAction, CommunicationChannel, CommunicationRequest


@dataclass
class CommunicationResult:
    status: str
    request: CommunicationRequest
    detail: str = ""


class CommunicationService:
    """Create and dispatch communication intents with explicit approval."""

    def __init__(self) -> None:
        self._adapters: Dict[str, Callable[[CommunicationRequest], str]] = {}

    def register_adapter(self, provider: str, handler: Callable[[CommunicationRequest], str]) -> None:
        if not provider.strip():
            raise ValueError("provider is required")
        self._adapters[provider] = handler

    def prepare(self, request: CommunicationRequest) -> CommunicationResult:
        self._validate(request)
        return CommunicationResult("prepared", request, "جاهز للتنفيذ بعد التأكيد")

    def dispatch(self, request: CommunicationRequest) -> CommunicationResult:
        self._validate(request)
        if request.requires_confirmation and not request.approved:
            return CommunicationResult("approval_required", request, "يلزم تأكيد المستخدم قبل الاتصال أو الإرسال")
        if request.action == CommunicationAction.PREPARE:
            return CommunicationResult("prepared", request)
        if not request.provider:
            return CommunicationResult("adapter_required", request, "لا يوجد مزود اتصال محدد")
        handler = self._adapters.get(request.provider)
        if handler is None:
            return CommunicationResult("adapter_required", request, f"المزود غير مربوط: {request.provider}")
        return CommunicationResult("sent", request, handler(request))

    @staticmethod
    def _validate(request: CommunicationRequest) -> None:
        if not request.recipient.strip():
            raise ValueError("recipient is required")
        if request.channel in {CommunicationChannel.SMS, CommunicationChannel.SOCIAL}:
            if not request.message or not request.message.strip():
                raise ValueError("message is required for messaging")
        if request.channel == CommunicationChannel.CALL and request.action != CommunicationAction.CALL:
            raise ValueError("call channel requires call action")
