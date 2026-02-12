"""Provider router with fallback order and privacy-aware logging."""

from __future__ import annotations

from app.models.schemas import ManualSearchSubmitRequest, SearchResponse
from app.services.audit import hash_text, log_event
from app.services.limits import RunLimiter, enforce_rate_limit
from app.services.policy_guard import assert_permission, policy_allows_action
from app.services.workspaces import get_active_workspace
from app.services.search_providers import (
    DuckDuckGoHtmlProvider,
    LocalBrowserProvider,
    ManualFallbackProvider,
)
from app.services.settings_service import get_effective_settings


async def search_with_router(
    query: str,
    num_results: int,
    safe: bool,
    session_id: str,
    manual_payload: ManualSearchSubmitRequest | None = None,
    safe_mode: bool = True,
    limiter: RunLimiter | None = None,
    run_id: str | None = None,
) -> SearchResponse:
    policy_ok, policy_reason = policy_allows_action("web.search")
    if not policy_ok:
        log_event(
            "policy.denied",
            "Policy denied web.search",
            {"tool": "web.search", "reason": policy_reason},
            session_id=session_id,
        )
        raise PermissionError(f"permission_required:policy:{policy_reason}")
    workspace = get_active_workspace()
    if workspace and workspace.get("allowed_tools"):
        if "web.search" not in workspace["allowed_tools"]:
            log_event(
                "workspace.denied",
                "Workspace denied web.search",
                {"tool": "web.search"},
                session_id=session_id,
            )
            raise PermissionError("permission_required:workspace:Web search not allowed by workspace")
    assert_permission("web.search", session_id=session_id, safe_mode=safe_mode)
    settings = get_effective_settings()
    query_hash = hash_text(query)
    manual = ManualFallbackProvider()

    if limiter:
        try:
            limiter.check_runtime()
            limiter.check_tool_call()
            enforce_rate_limit(session_id, limiter.max_tool_calls_per_minute)
            limiter.record_tool_call()
        except RuntimeError as exc:
            log_event(
                "limit.blocked",
                "Web search blocked by limits",
                {"tool": "web.search", "reason": str(exc)},
                session_id=session_id,
            )
            raise

    if manual_payload:
        parsed = manual.parse_manual(manual_payload)
        _log_search(query, query_hash, parsed.provider, len(parsed.results), parsed.status == "ok", run_id=run_id)
        return SearchResponse(
            status=parsed.status, provider=parsed.provider, results=parsed.results, detail=parsed.detail, manual_instructions=parsed.manual_instructions
        )

    if settings.search_provider == "manual":
        fallback = await manual.search(query=query, num_results=num_results, safe=safe)
        _log_search(query, query_hash, fallback.provider, 0, False, run_id=run_id)
        return SearchResponse(
            status="manual_required",
            provider=fallback.provider,
            results=[],
            detail=fallback.detail,
            manual_instructions=fallback.manual_instructions,
        )

    providers = []
    if settings.search_provider == "local_browser" and settings.local_browser_enabled:
        providers.append(LocalBrowserProvider(headed=settings.local_browser_headed, engine=settings.local_browser_engine))
        providers.append(DuckDuckGoHtmlProvider())
    else:
        providers.append(DuckDuckGoHtmlProvider())
        if settings.local_browser_enabled:
            providers.append(LocalBrowserProvider(headed=settings.local_browser_headed, engine=settings.local_browser_engine))

    for provider in providers:
        result = await provider.search(query=query, num_results=num_results, safe=safe)
        if result.status == "ok":
            _log_search(query, query_hash, result.provider, len(result.results), True, run_id=run_id)
            return SearchResponse(status="ok", provider=result.provider, results=result.results, detail=result.detail)

    fallback = await manual.search(query=query, num_results=num_results, safe=safe)
    _log_search(query, query_hash, fallback.provider, 0, False, run_id=run_id)
    return SearchResponse(
        status="manual_required",
        provider=fallback.provider,
        results=[],
        detail=fallback.detail,
        manual_instructions=fallback.manual_instructions,
    )


async def test_search_provider(session_id: str) -> SearchResponse:
    # Uses a harmless query and still requires permission.
    return await search_with_router(
        query="example domain",
        num_results=3,
        safe=True,
        session_id=session_id,
        manual_payload=None,
        safe_mode=False,
    )


def _log_search(query: str, query_hash: str, provider: str, num_results: int, success: bool, run_id: str | None = None) -> None:
    settings = get_effective_settings()
    payload = {
        "provider": provider,
        "query_hash": query_hash,
        "num_results": num_results,
        "success": success,
    }
    if not settings.privacy_mode and settings.allow_query_text_logging:
        payload["query"] = query
    log_event("search.execute", f"Search via {provider}", payload=payload)
    if run_id:
        from app.services.run_logger import log_run_event
        log_run_event(run_id, "search.execute", payload)
