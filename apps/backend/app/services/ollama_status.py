"""Local Ollama readiness checks with cached status and snooze state."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.db.sqlite import connection
from app.services.audit import log_event
from app.services.settings_service import get_effective_settings


OLLAMA_INSTALL_URL = "https://ollama.com/download/windows"
OLLAMA_DEFAULT_BASE = "http://127.0.0.1:11434"
_status_lock = asyncio.Lock()
_status_cache: dict[str, Any] = {
    "installed": False,
    "healthy": False,
    "models_count": 0,
    "last_checked_at": datetime.now(timezone.utc).isoformat(),
}


def _read_runtime_value(key: str) -> str | None:
    with connection() as conn:
        row = conn.execute("SELECT value_json FROM app_settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["value_json"])
    except Exception:
        return None


def _write_runtime_value(key: str, value: Any) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO app_settings (key, value_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=CURRENT_TIMESTAMP
            """,
            (key, json.dumps(value)),
        )


async def probe_local_ollama() -> dict[str, Any]:
    settings = get_effective_settings()
    installed = False
    healthy = False
    models_count = 0
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_DEFAULT_BASE}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models_count = len(data.get("models", []))
            installed = True
            healthy = True
    except Exception:
        installed = False
        healthy = False
        models_count = 0
    fallback_mode_active = bool(settings.ollama_required_for_local_chat and not healthy)
    return {
        "installed": installed,
        "healthy": healthy,
        "models_count": models_count,
        "last_checked_at": datetime.now(timezone.utc).isoformat(),
        "next_check_in_seconds": int(settings.ollama_check_interval_seconds),
        "fallback_mode_active": fallback_mode_active,
    }


async def refresh_ollama_status() -> dict[str, Any]:
    async with _status_lock:
        status = await probe_local_ollama()
        _status_cache.update(status)
        return dict(_status_cache)


def get_cached_ollama_status() -> dict[str, Any]:
    status = dict(_status_cache)
    settings = get_effective_settings()
    status["next_check_in_seconds"] = int(settings.ollama_check_interval_seconds)
    status["fallback_mode_active"] = bool(settings.ollama_required_for_local_chat and not bool(status.get("healthy")))
    snooze_until = _read_runtime_value("ollama.install_prompt_snooze_until")
    suppressed = False
    if isinstance(snooze_until, str):
        try:
            suppressed = datetime.now(timezone.utc) < datetime.fromisoformat(snooze_until.replace("Z", "+00:00"))
        except Exception:
            suppressed = False
    status["install_prompt_suppressed"] = suppressed
    status["install_prompt_suppressed_until"] = snooze_until
    return status


def remind_later(minutes: int) -> dict[str, Any]:
    minutes = max(1, int(minutes))
    until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    _write_runtime_value("ollama.install_prompt_snooze_until", until)
    log_event("ollama.install.remind_later", "Ollama install prompt snoozed", {"minutes": minutes})
    return {"status": "ok", "remind_after_minutes": minutes}


def record_install_prompt() -> dict[str, Any]:
    log_event("ollama.install.prompt", "Prompted user to install Ollama", {"url": OLLAMA_INSTALL_URL})
    return {"launched": True, "url": OLLAMA_INSTALL_URL, "detail": "Open this URL to install Ollama for local model support."}
