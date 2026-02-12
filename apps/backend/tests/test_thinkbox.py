import pytest

from app.models.schemas import ThinkBoxMessageRequest
from app.services import thinkbox


@pytest.mark.anyio
async def test_thinkbox_stream_buffers_tokens(monkeypatch) -> None:
    async def fake_stream_chat(payload, session_id):  # noqa: ANN001
        yield '{"type":"run_started","run_id":"run-1"}'
        yield '{"type":"token","content":"A"}'
        yield '{"type":"token","content":"B"}'

    monkeypatch.setattr("app.services.thinkbox.stream_chat", fake_stream_chat)
    monkeypatch.setattr("app.services.thinkbox.list_model_options", lambda: _fake_models())

    req = ThinkBoxMessageRequest(text="hello", mode="screen_help", toggles={"safe_mode": True}, context={})
    run_id = await thinkbox.submit_thinkbox_message(req, session_id="s1")
    assert run_id == "run-1"
    events, cursor, done = thinkbox.read_thinkbox_stream("run-1", 0)
    assert len(events) >= 2
    assert cursor >= 2
    assert done is True


@pytest.mark.anyio
async def test_thinkbox_research_uses_search_router(monkeypatch) -> None:
    called = {"search": False}

    async def fake_search_with_router(**kwargs):  # noqa: ANN003
        called["search"] = True
        class Result:  # simple stub
            status = "ok"
            results = []
        return Result()

    async def fake_stream_chat(payload, session_id):  # noqa: ANN001
        assert "manual input" in payload.message.lower() or "user request" in payload.message.lower()
        yield '{"type":"run_started","run_id":"run-2"}'

    monkeypatch.setattr("app.services.thinkbox.search_with_router", fake_search_with_router)
    monkeypatch.setattr("app.services.thinkbox.stream_chat", fake_stream_chat)
    monkeypatch.setattr("app.services.thinkbox.list_model_options", lambda: _fake_models())

    req = ThinkBoxMessageRequest(text="example domain", mode="research", toggles={"safe_mode": False}, context={})
    run_id = await thinkbox.submit_thinkbox_message(req, session_id="s1")
    assert run_id == "run-2"
    assert called["search"] is True


async def _fake_models():
    class Model:
        source_id = "local-ollama"
        model = "llama3.1:8b"

    return [Model()]
