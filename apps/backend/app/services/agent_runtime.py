"""Agent runtime for chat mode with policy-enforced tool/search boundaries."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from app.models.schemas import ChatRequest
from app.services.audit import log_event
from app.services.model_sources import get_source
from app.services.ollama_client import stream_ollama_chat
from app.services.limits import build_run_limiter
from app.services.search_router import search_with_router
from app.services.secret_store import get_secret
from app.services.settings_service import get_effective_settings
from app.services.tool_runner import run_tool
from app.services.run_logger import finish_run, log_run_event, start_run
from app.services.memory import list_memory
from app.services.intent_router import classify_intent
from app.services.runtime_fallback import decide_runtime_route


async def stream_chat(payload: ChatRequest, session_id: str) -> AsyncGenerator[str, None]:
    route = await decide_runtime_route(payload.source_id, payload.model)
    if route.get("mode") == "remote_switch":
        payload.source_id = route["source_id"]
        payload.model = route["model"]
        yield json.dumps({"type": "fallback_mode", "mode": "remote_switch", "reason": route.get("reason", "")})
    elif route.get("mode") == "search_answer":
        yield json.dumps({"type": "fallback_mode", "mode": "search_answer", "reason": route.get("reason", "")})
    elif route.get("mode") == "blocked":
        yield json.dumps({"type": "error", "detail": f"Ollama unavailable: {route.get('reason', 'blocked')}"})
        return

    source = get_source(payload.source_id)
    if not source:
        yield json.dumps({"type": "error", "detail": "Model source not found"})
        return

    safe_mode = bool(payload.context.get("safe_mode", True))
    settings = get_effective_settings()
    run = start_run(
        session_id=session_id,
        mode="chat",
        input_text=payload.message,
        model_source_id=payload.source_id,
        model_name=payload.model,
    )
    run_id = run["id"]
    yield json.dumps({"type": "run_started", "run_id": run_id})
    intent = classify_intent(payload.message)
    log_run_event(run_id, "intent", {"intent": intent})
    limiter = build_run_limiter(
        {
            "max_tool_calls_per_message": settings.max_tool_calls_per_message,
            "max_tool_calls_per_minute": settings.max_tool_calls_per_minute,
            "max_files_read_per_run": settings.max_files_read_per_run,
            "max_bytes_read_per_run": settings.max_bytes_read_per_run,
            "max_runtime_seconds": settings.max_runtime_seconds,
        },
        session_id=session_id,
    )
    text = payload.message.strip()
    lower = text.lower()

    if route.get("mode") == "search_answer":
        query = text or "latest information"
        try:
            search = await search_with_router(
                query=query,
                num_results=5,
                safe=True,
                session_id=session_id,
                safe_mode=safe_mode,
                limiter=limiter,
                run_id=run_id,
            )
        except PermissionError as exc:
            perm = str(exc).split(":")[1] if ":" in str(exc) else "web.search"
            log_run_event(run_id, "permission.required", {"permission": perm})
            yield json.dumps({"type": "permission_required", "permission": perm})
            finish_run(run_id, run["start"])
            return
        if search.status == "manual_required":
            log_run_event(run_id, "manual_search_required", {"query": query})
            yield json.dumps(
                {
                    "type": "manual_search_required",
                    "query": query,
                    "instructions": search.manual_instructions or "Paste manual results in Settings/Search UI.",
                }
            )
            finish_run(run_id, run["start"])
            return
        lines = [f"- {item.title} ({item.url}) {item.snippet}" for item in search.results]
        answer = "Local Ollama is unavailable. Using web search fallback:\n" + "\n".join(lines)
        log_run_event(run_id, "fallback.answer", {"provider": search.provider, "count": len(search.results)})
        yield json.dumps({"type": "token", "content": answer})
        finish_run(run_id, run["start"])
        return

    # Deterministic tool routes keep permissions outside model control.
    if lower.startswith("read file:"):
        path = text.split(":", 1)[1].strip()
        try:
            tool_result = run_tool(
                "file_read",
                {"path": path},
                session_id=session_id,
                safe_mode=safe_mode,
                mode="chat",
                limiter=limiter,
                run_id=run_id,
            )
            payload.message = f"Summarize this file:\n{tool_result.get('content', '')[:6000]}"
        except PermissionError as exc:
            perm = str(exc).split(":")[1] if ":" in str(exc) else "filesystem.read"
            log_run_event(run_id, "permission.required", {"permission": perm})
            yield json.dumps({"type": "permission_required", "permission": perm})
            finish_run(run_id, run["start"])
            return
        except Exception as exc:
            log_run_event(run_id, "error", {"detail": str(exc)})
            yield json.dumps({"type": "error", "detail": str(exc)})
            finish_run(run_id, run["start"])
            return

    if lower.startswith("search web:"):
        query = text.split(":", 1)[1].strip()
        try:
            search = await search_with_router(
                query=query,
                num_results=5,
                safe=True,
                session_id=session_id,
                safe_mode=safe_mode,
                limiter=limiter,
                run_id=run_id,
            )
        except PermissionError as exc:
            perm = str(exc).split(":")[1] if ":" in str(exc) else "web.search"
            log_run_event(run_id, "permission.required", {"permission": perm})
            yield json.dumps({"type": "permission_required", "permission": perm})
            finish_run(run_id, run["start"])
            return
        if search.status == "manual_required":
            log_run_event(run_id, "manual_search_required", {"query": query})
            yield json.dumps(
                {
                    "type": "manual_search_required",
                    "query": query,
                    "instructions": search.manual_instructions or "Paste manual results in Settings/Search UI.",
                }
            )
            finish_run(run_id, run["start"])
            return
        results_block = "\n".join([f"- {item.title} ({item.url}) {item.snippet}" for item in search.results])
        payload.message = f"Use these web search results to answer:\n{results_block}"

    log_event(
        "model.usage",
        f"Model chat using {payload.model}",
        {"source_id": payload.source_id, "model": payload.model, "mode": payload.mode},
        session_id=session_id,
    )

    if settings.use_saved_memory:
        memories = list_memory()
        if memories:
            mem_block = "\n".join([f"- ({m['kind']}) {m['content']}" for m in memories])
            payload.message = f"Use these saved memory items as context:\n{mem_block}\n\nUser message:\n{payload.message}"

    token = get_secret(f"model_source:{source.id}:auth_token")
    full_output = ""
    try:
        async for chunk in stream_ollama_chat(base_url=source.base_url, model=payload.model, message=payload.message, auth_token=token):
            full_output += chunk
            yield json.dumps({"type": "token", "content": chunk})
    except Exception as exc:
        log_run_event(run_id, "error", {"detail": str(exc)})
        yield json.dumps({"type": "error", "detail": str(exc)})
    finally:
        if settings.reviewer_enabled:
            warnings = []
            if settings.reviewer_strictness in {"standard", "strict"}:
                if "http" not in full_output and "https" not in full_output and "search" in payload.message.lower():
                    warnings.append("Response lacks citations for a search-based answer.")
            if settings.reviewer_strictness == "strict":
                if "permission" in full_output.lower():
                    warnings.append("Response mentions permissions; verify no policy bypass guidance.")
            review = {"warnings": warnings, "strictness": settings.reviewer_strictness}
            log_run_event(run_id, "review", review)
            yield json.dumps({"type": "review", "warnings": warnings})
        finish_run(run_id, run["start"])
