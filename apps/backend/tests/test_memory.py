from app.services.memory import create_memory, delete_memory, list_memory, update_memory


def test_memory_crud() -> None:
    item = create_memory("preference", "Likes concise answers")
    assert item["kind"] == "preference"
    updated = update_memory(item["id"], "Likes detailed answers")
    assert updated["content"] == "Likes detailed answers"
    items = list_memory()
    assert any(x["id"] == item["id"] for x in items)
    delete_memory(item["id"])
