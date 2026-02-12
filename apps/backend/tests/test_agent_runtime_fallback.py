import json

import pytest

from app.models.schemas import ChatRequest
from app.services.agent_runtime import stream_chat


@pytest.mark.anyio
async def test_agent_runtime_emits_search_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.agent_runtime.decide_runtime_route",
        lambda _source_id, _model: _async_value({"mode": "search_answer", "reason": "ollama_unavailable"}),
    )
    monkeypatch.setattr(
        "app.services.agent_runtime.get_source",
        lambda _sid: type("Source", (), {"id": "local-ollama", "base_url": "http://127.0.0.1:11434"})(),
    )
    monkeypatch.setattr(
        "app.services.agent_runtime.search_with_router",
        lambda **kwargs: _async_value(
            type(
                "SearchResult",
                (),
                {
                    "status": "ok",
                    "provider": "duckduckgo_html",
                    "results": [
                        type("Item", (), {"title": "Example", "url": "https://example.com", "snippet": "example snippet"})()
                    ],
                },
            )()
        ),
    )
    payload = ChatRequest(source_id="local-ollama", model="llama3", message="what is example", mode="chat", context={"safe_mode": False})
    events = []
    async for chunk in stream_chat(payload, session_id="s1"):
        events.append(json.loads(chunk))
    assert any(item.get("type") == "fallback_mode" for item in events)
    assert any(item.get("type") == "token" for item in events)


async def _async_value(value):
    return value
