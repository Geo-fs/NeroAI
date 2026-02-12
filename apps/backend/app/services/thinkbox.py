"""Think Box runtime orchestration and stream helpers."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.models.schemas import ChatRequest, ThinkBoxMessageRequest
from app.services.agent_runtime import stream_chat
from app.services.model_sources import list_model_options
from app.services.search_router import search_with_router
from app.services.settings_service import get_effective_settings


_STREAM_CACHE: dict[str, dict[str, Any]] = {}


def _mode_prompt(mode: str, text: str, context: dict[str, Any]) -> str:
    frozen_capture_id = context.get("frozen_capture_id")
    selected_text = context.get("selected_text", "")
    clipboard_text = context.get("clipboard_text", "")
    base = f"User request: {text}\n"
    if frozen_capture_id:
        base += f"Capture reference id: {frozen_capture_id}\n"
    if selected_text:
        base += f"Selected text:\n{selected_text}\n"
    if clipboard_text:
        base += f"Clipboard text:\n{clipboard_text}\n"
    if mode == "steps":
        return "Provide concise numbered steps.\n" + base
    if mode == "extract":
        return "Extract key entities and facts as bullets.\n" + base
    if mode == "explain":
        return "Explain clearly in short bullets.\n" + base
    if mode == "research":
        return "Use citations where possible.\n" + base
    return "Help with what is visible on screen in concise bullets.\n" + base


async def _run_thinkbox(req: ThinkBoxMessageRequest, session_id: str, run_id_hint: str | None = None) -> str:
    source_id = req.model_source_id
    model = req.model
    if not source_id or not model:
        options = await list_model_options()
        if options:
            source_id = source_id or options[0].source_id
            model = model or options[0].model
        else:
            source_id = source_id or "local-ollama"
            model = model or "llama3.1:8b"

    prompt = _mode_prompt(req.mode, req.text, req.context)
    if req.mode == "research":
        settings = get_effective_settings()
        try:
            search = await search_with_router(
                query=req.text,
                num_results=5,
                safe=True,
                session_id=session_id,
                safe_mode=settings.safe_mode_default,
            )
            if search.results:
                refs = "\n".join([f"- {r.title} ({r.url}) {r.snippet}" for r in search.results])
                prompt += f"\nSearch results:\n{refs}\n"
            elif search.status == "manual_required":
                prompt += (
                    "\nSearch provider requested manual input. "
                    "Ask the user to paste manual search results as title/url/snippet."
                )
        except Exception:
            pass

    safe_mode = bool(req.toggles.get("safe_mode", True))
    payload = ChatRequest(
        source_id=source_id,
        model=model,
        message=prompt,
        mode="chat",
        context={
            "safe_mode": safe_mode,
            "thinkbox": True,
            "thinkbox_mode": req.mode,
            "multi_agent": bool(req.toggles.get("multi_agent", False)),
        },
    )

    run_id = run_id_hint or ""
    async for chunk in stream_chat(payload, session_id=session_id):
        data = json.loads(chunk)
        if data.get("type") == "run_started":
            run_id = data.get("run_id", "")
            _STREAM_CACHE.setdefault(run_id, {"events": [], "done": False})
        if run_id:
            _STREAM_CACHE.setdefault(run_id, {"events": [], "done": False})
            _STREAM_CACHE[run_id]["events"].append(data)
        if data.get("type") == "error":
            break
    if run_id:
        _STREAM_CACHE.setdefault(run_id, {"events": [], "done": False})
        _STREAM_CACHE[run_id]["done"] = True
    return run_id


async def submit_thinkbox_message(req: ThinkBoxMessageRequest, session_id: str) -> str:
    known_ids = set(_STREAM_CACHE.keys())
    task = asyncio.create_task(_run_thinkbox(req, session_id=session_id))
    for _ in range(120):
        await asyncio.sleep(0.05)
        for run_id, item in _STREAM_CACHE.items():
            if run_id in known_ids:
                continue
            if item["events"]:
                if item["events"][0].get("type") == "run_started":
                    return run_id
    run_id = await task
    return run_id


def read_thinkbox_stream(run_id: str, cursor: int) -> tuple[list[dict[str, Any]], int, bool]:
    item = _STREAM_CACHE.get(run_id, {"events": [], "done": False})
    events = item["events"]
    next_cursor = len(events)
    slice_events = events[cursor:next_cursor] if cursor < next_cursor else []
    return slice_events, next_cursor, bool(item.get("done", False))
