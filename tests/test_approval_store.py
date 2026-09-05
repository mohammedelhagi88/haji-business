from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from core.approval_store import PersistentApprovalStore


def test_approval_survives_reopen(tmp_path):
    db = tmp_path / "haji.sqlite3"
    store = PersistentApprovalStore(str(db))
    store.put("abc", "trade BUY BTCUSDT", "financial", "test", {"symbol": "BTCUSDT"})
    store.close()

    reopened = PersistentApprovalStore(str(db))
    record = reopened.consume("abc")
    assert record["payload"]["symbol"] == "BTCUSDT"
    assert reopened.consume("abc") is None
    reopened.close()


def test_expired_approval_is_rejected(tmp_path):
    db = tmp_path / "haji.sqlite3"
    store = PersistentApprovalStore(str(db), ttl_seconds=60)
    store.put("old", "trade", "financial", "test", {})
    with store._lock:
        store._db.execute("UPDATE approvals SET created_at=? WHERE approval_id=?", ((datetime.utcnow() - timedelta(hours=1)).isoformat(), "old"))
        store._db.commit()
    assert store.consume("old") is None
    store.close()


def test_approval_is_consumed_only_once_under_concurrency(tmp_path):
    db = tmp_path / "haji.sqlite3"
    store = PersistentApprovalStore(str(db))
    store.put("once", "trade", "financial", "test", {"symbol": "BTCUSDT"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(store.consume, ["once"] * 8))
    assert sum(result is not None for result in results) == 1
    store.close()
