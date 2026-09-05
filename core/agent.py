"""Haji agent orchestration and Libyan-Arabic intent routing."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from .ai_provider import AIProvider
from .approval_store import PersistentApprovalStore
from .commands import CommandEngine
from .memory import MemoryStore
from .models import ApprovalRequest, RiskLevel, Task
from .permissions import PermissionGate
from .runtime import HajiRuntime, RuntimeEvent
from .tasks import TaskManager


class HajiAgent:
    """Agent with local commands, persistent context, optional AI, and safety gates."""

    def __init__(
        self,
        memory: MemoryStore | Any | None = None,
        tasks: TaskManager | None = None,
        runtime: HajiRuntime | None = None,
        permissions: PermissionGate | None = None,
        provider: AIProvider | None = None,
        approval_store: PersistentApprovalStore | None = None,
    ) -> None:
        self.memory = memory or MemoryStore()
        self.tasks = tasks or TaskManager()
        self.runtime = runtime or HajiRuntime()
        self.permissions = permissions or PermissionGate()
        self.commands = CommandEngine(self.permissions)
        self.provider = provider
        self.approval_store = approval_store
        self._approvals: dict[str, ApprovalRequest] = {}

    @staticmethod
    def _has(text: str, *words: str) -> bool:
        return any(word in text for word in words)

    def _financial_request(self) -> tuple[str, ApprovalRequest]:
        request = self.permissions.request_approval(
            action="financial_or_sensitive_action",
            risk=RiskLevel.FINANCIAL,
            reason="الأمر ممكن يسبب التزام مالي؛ نحتاج موافقتك الصريحة قبل التنفيذ.",
        )
        approval_id = uuid4().hex
        self._approvals[approval_id] = request
        if self.approval_store is not None:
            self.approval_store.put(approval_id, request.action, request.risk.value, request.reason, {})
        return approval_id, request

    def approve(self, approval_id: str) -> dict[str, Any]:
        if self.approval_store is not None:
            record = self.approval_store.consume(approval_id)
            if record is None:
                return {"ok": False, "error": "approval_not_found_or_expired"}
            request = ApprovalRequest(
                action=record["action"],
                risk=RiskLevel(record["risk"]),
                reason=record["reason"],
                created_at=datetime.fromisoformat(record["created_at"]),
                approved=False,
            )
        else:
            request = self._approvals.pop(approval_id, None)
            if request is None:
                return {"ok": False, "error": "approval_not_found"}

        self.permissions.approve(request)
        self.runtime.emit(RuntimeEvent("approval.granted", {"approval_id": approval_id}))
        return {"ok": True, "approvalId": approval_id, "approval": asdict(request)}

    def handle(self, text: str = "", image: bytes | None = None) -> dict[str, Any]:
        text = (text or "").strip()
        self.runtime.emit(RuntimeEvent("agent.message", {"text": text, "has_image": image is not None}))
        if text:
            self.memory.set("last_user_message", text)

        if self._has(text, "اشترى", "شراء", "بيع", "صفقة", "تداول", "حول", "تحويل", "ادفع", "دفع"):
            approval_id, request = self._financial_request()
            return {
                "text": "نقدر نحلل ونجهزلك العملية، لكن التنفيذ المالي يحتاج موافقتك الصريحة أولاً.",
                "requiresApproval": True,
                "approvalId": approval_id,
                "approval": asdict(request),
            }

        if self._has(text, "ديرلي مهمة", "ضيف مهمة", "أضف مهمة", "ذكرني", "مهمة"):
            title = text
            for prefix in ("ديرلي مهمة", "ضيف مهمة", "أضف مهمة", "ذكرني"):
                title = title.replace(prefix, "", 1).strip()
            task = self.tasks.add(Task(title=title or "مهمة جديدة"))
            return {"text": f"تم، ضفتلك المهمة: {task.title}", "requiresApproval": False, "task": asdict(task)}

        if self._has(text, "شن المهام", "المهام", "قائمة المهام", "مهامي"):
            items = self.tasks.list()
            return {
                "text": "ما عندكش مهام مسجلة حالياً." if not items else "هذي مهامك: " + "، ".join(f"{i + 1}. {t.title}" for i, t in enumerate(items)),
                "requiresApproval": False,
                "tasks": [asdict(t) for t in items],
            }

        if self._has(text, "احفظ", "خلي في بالك"):
            value = text
            for prefix in ("احفظ", "خلي في بالك"):
                value = value.replace(prefix, "", 1).strip()
            self.memory.set("user_note", value)
            return {"text": f"حاضر، حفظتها: {value}", "requiresApproval": False}

        if self._has(text, "شن قلتلك آخر مرة", "آخر رسالة", "تذكر آخر"):
            last = self.memory.get("last_user_message")
            return {"text": f"آخر حاجة قلتها هي: {last}" if last else "ما عنديش رسالة محفوظة قبل هذي.", "requiresApproval": False}

        if self.provider is not None and (text or image):
            try:
                answer = self.provider.chat(text or "حلل الصورة ووضحلي محتواها.", image)
                return {"text": answer, "requiresApproval": False, "ai": True}
            except Exception as exc:
                self.runtime.emit(RuntimeEvent("agent.provider_error", {"error": str(exc)}))

        if image is not None:
            return {"text": f"وصلتني الصورة{('، وطلبك: ' + text) if text else ''}. مزود الرؤية مش مفعّل حالياً.", "requiresApproval": False}
        return {"text": f"فهمتك يا حاجي: {text}" if text else "قولّي شن تبي نديرلك.", "requiresApproval": False}
