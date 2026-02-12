"""Audit logger with privacy-aware redaction defaults."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from app.db.sqlite import connection
from app.services.settings_service import get_effective_settings

SENSITIVE_KEYS = {"token", "auth", "authorization", "password", "secret", "api_key", "key"}


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if any(part in key.lower() for part in SENSITIVE_KEYS):
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str) and len(value) > 2048:
        return value[:2048] + "...<truncated>"
    return value


def log_event(
    event_type: str,
    summary: str,
    payload: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> None:
    settings = get_effective_settings()
    data = payload or {}
    if settings.redaction_enabled:
        data = _redact(data)
    if not settings.verbose_logging:
        # Keep default logs minimal and safe.
        data = {k: data[k] for k in ("provider", "query_hash", "success", "num_results", "tool", "result_hash") if k in data}
    with connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (id, session_id, event_type, summary, payload_json) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, event_type, summary, json.dumps(data)),
        )


def list_audit_logs(limit: int = 200) -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, session_id, event_type, summary, payload_json, created_at FROM audit_logs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json") or "{}")
        output.append(item)
    return output
