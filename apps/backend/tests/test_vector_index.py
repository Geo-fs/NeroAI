from app.services.vector_index import index_documents, search_index


def test_vector_index_basic() -> None:
    workspace_id = "ws1"
    index_documents(workspace_id, [{"path": "a.txt", "content": "hello world", "content_hash": "x"}])
    results = search_index(workspace_id, "hello", limit=3)
    assert results
    assert results[0]["path"] == "a.txt"
