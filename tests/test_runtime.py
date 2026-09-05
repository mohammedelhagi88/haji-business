from datetime import datetime, timezone

import pytest

from core.runtime import HajiRuntime, RuntimeEvent


def test_event_handlers_run_on_emit():
    runtime = HajiRuntime()
    seen = []
    runtime.on("notification", lambda payload: seen.append(payload["text"]))

    result = runtime.emit(RuntimeEvent("notification", {"text": "hello"}))

    assert result == [None]
    assert seen == ["hello"]


def test_scheduled_module_runs_when_due_only():
    runtime = HajiRuntime()
    calls = []
    runtime.schedule("market", 10, lambda payload: calls.append(payload["runtime_time"]))
    start = runtime._scheduled["market"].next_run

    runtime.tick(start)
    runtime.tick(start.replace(second=start.second + 5))
    runtime.tick(start.replace(second=start.second + 10))

    assert len(calls) == 2


def test_schedule_rejects_invalid_interval():
    with pytest.raises(ValueError):
        HajiRuntime().schedule("bad", 0, lambda _: None)
