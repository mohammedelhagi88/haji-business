from core.persistent_memory import PersistentMemoryStore


def test_memory_survives_new_store(tmp_path):
    path = str(tmp_path / "memory.sqlite3")
    first = PersistentMemoryStore(path)
    first.set("user_note", "الخطة واضحة")
    first.close()

    second = PersistentMemoryStore(path)
    assert second.get("user_note") == "الخطة واضحة"
    assert second.delete("user_note") is True
    assert second.get("user_note") is None
    second.close()
