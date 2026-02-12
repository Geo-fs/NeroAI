"""Runtime source fallback decisions for local Ollama readiness."""

from __future__ import annotations

from typing import Any

from app.services.model_sources import get_source, list_model_options
from app.services.ollama_status import get_cached_ollama_status
from app.services.settings_service import get_effective_settings


async def decide_runtime_route(source_id: str, model: str) -> dict[str, Any]:
    settings = get_effective_settings()
    source = get_source(source_id)
    if not source:
        return {"mode": "normal", "source_id": source_id, "model": model}

    status = get_cached_ollama_status()
    local_unavailable = bool(source.is_local and settings.ollama_required_for_local_chat and not status.get("healthy", False))
    if not local_unavailable:
        return {"mode": "normal", "source_id": source_id, "model": model}

    fallback_mode = settings.ollama_fallback_mode
    options = await list_model_options()
    remote_options = [opt for opt in options if opt.source_id != source_id]
    if remote_options:
        selected = next((item for item in remote_options if item.model == model), remote_options[0])
        return {
            "mode": "remote_switch",
            "source_id": selected.source_id,
            "model": selected.model,
            "reason": "ollama_unavailable_switched_remote",
        }

    if fallback_mode == "search_answer":
        return {"mode": "search_answer", "source_id": source_id, "model": model, "reason": "ollama_unavailable"}

    if fallback_mode == "remote_only":
        return {"mode": "blocked", "source_id": source_id, "model": model, "reason": "ollama_unavailable_no_remote"}

    return {"mode": "blocked", "source_id": source_id, "model": model, "reason": "ollama_required"}
