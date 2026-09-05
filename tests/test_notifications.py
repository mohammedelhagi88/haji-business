from core.notifications import NotificationService
from core.runtime import HajiRuntime, RuntimeEvent


def test_agent_message_notification_uses_text_payload():
    runtime = HajiRuntime()
    service = NotificationService(runtime)
    runtime.emit(RuntimeEvent("agent.message", {"text": "هلا يا حاجي"}))
    history = service.history()
    assert len(history) == 1
    assert history[0].message == "هلا يا حاجي"
