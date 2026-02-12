import pytest

from app.services.runtime_fallback import decide_runtime_route


class _Source:
    def __init__(self, is_local: bool):
        self.is_local = is_local


class _Option:
    def __init__(self, source_id: str, model: str):
        self.source_id = source_id
        self.model = model


class _Settings:
    def __init__(self, fallback_mode: str = "search_answer"):
        self.ollama_required_for_local_chat = True
        self.ollama_fallback_mode = fallback_mode


@pytest.mark.anyio
async def test_runtime_fallback_to_search(monkeypatch) -> None:
    monkeypatch.setattr("app.services.runtime_fallback.get_source", lambda _sid: _Source(True))
    monkeypatch.setattr("app.services.runtime_fallback.get_cached_ollama_status", lambda: {"healthy": False})
    monkeypatch.setattr("app.services.runtime_fallback.get_effective_settings", lambda: _Settings("search_answer"))
    async def empty_options():
        return []
    monkeypatch.setattr("app.services.runtime_fallback.list_model_options", empty_options)
    route = await decide_runtime_route("local-ollama", "llama3")
    assert route["mode"] == "search_answer"


@pytest.mark.anyio
async def test_runtime_fallback_to_remote(monkeypatch) -> None:
    monkeypatch.setattr("app.services.runtime_fallback.get_source", lambda _sid: _Source(True))
    monkeypatch.setattr("app.services.runtime_fallback.get_cached_ollama_status", lambda: {"healthy": False})
    monkeypatch.setattr("app.services.runtime_fallback.get_effective_settings", lambda: _Settings("search_answer"))
    async def options():
        return [_Option("remote1", "qwen2.5")]
    monkeypatch.setattr("app.services.runtime_fallback.list_model_options", options)
    route = await decide_runtime_route("local-ollama", "llama3")
    assert route["mode"] == "remote_switch"
    assert route["source_id"] == "remote1"
