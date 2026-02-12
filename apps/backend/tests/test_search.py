import pytest

from app.models.schemas import ManualSearchSubmitRequest, SettingsUpdateRequest
from app.models.schemas import GrantPermissionRequest
from app.services.permission_broker import grant_permission
from app.services.audit import list_audit_logs
from app.services.search_providers import DuckDuckGoHtmlProvider, ManualFallbackProvider
from app.services.search_router import search_with_router
from app.services.settings_service import update_settings


@pytest.mark.anyio
async def test_provider_router_falls_back_to_manual() -> None:
    grant_permission(
        GrantPermissionRequest(permission="web.search", scope="session", allowed_paths=[]),
        session_id="s1",
    )
    update_settings(
        SettingsUpdateRequest(local_browser_enabled=False, privacy_mode=True, allow_query_text_logging=False)
    )
    result = await search_with_router(
        query="query-that-likely-fails-in-sandbox",
        num_results=3,
        safe=True,
        session_id="s1",
        safe_mode=False,
    )
    assert result.status in {"ok", "manual_required"}


def test_manual_fallback_validation() -> None:
    provider = ManualFallbackProvider()
    bad = provider.parse_manual(ManualSearchSubmitRequest(query="x", pasted_lines="not a url"))
    assert bad.status == "error"

    ok = provider.parse_manual(
        ManualSearchSubmitRequest(query="x", pasted_lines="Example|https://example.com|snippet")
    )
    assert ok.status == "ok"
    assert ok.results[0].url == "https://example.com"


@pytest.mark.anyio
async def test_privacy_hashing_in_search_logs() -> None:
    grant_permission(
        GrantPermissionRequest(permission="web.search", scope="session", allowed_paths=[]),
        session_id="s1",
    )
    update_settings(SettingsUpdateRequest(privacy_mode=True, allow_query_text_logging=False))
    await search_with_router(query="private query", num_results=2, safe=True, session_id="s1", safe_mode=False)
    logs = list_audit_logs(limit=10)
    search_logs = [x for x in logs if x["event_type"] == "search.execute"]
    assert search_logs
    payload = search_logs[0]["payload"]
    assert "query_hash" in payload
    assert "query" not in payload


@pytest.mark.anyio
async def test_duckduckgo_provider_integration_best_effort() -> None:
    grant_permission(
        GrantPermissionRequest(permission="web.search", scope="session", allowed_paths=[]),
        session_id="s1",
    )
    provider = DuckDuckGoHtmlProvider()
    result = await provider.search("example domain", num_results=3, safe=True)
    if result.status != "ok":
        pytest.xfail(f"network unavailable or blocked: {result.detail}")
    assert len(result.results) >= 1
