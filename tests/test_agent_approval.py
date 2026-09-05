from core.agent import HajiAgent
from core.approval_store import PersistentApprovalStore


def test_agent_approval_is_persistent_and_one_time(tmp_path):
    db = tmp_path / "haji.sqlite3"
    store = PersistentApprovalStore(str(db))

    first = HajiAgent(approval_store=store)
    pending = first.handle("نفذ صفقة")
    approval_id = pending["approvalId"]

    second = HajiAgent(approval_store=store)
    approved = second.approve(approval_id)
    assert approved["ok"] is True
    assert approved["approval"]["approved"] is True

    replay = first.approve(approval_id)
    assert replay["ok"] is False
    assert replay["error"] == "approval_not_found_or_expired"
    store.close()
