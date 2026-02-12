"""Run logging for session replay and run reports."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from app.db.sqlite import connection
from app.services.audit import hash_text
from app.services.settings_service import get_effective_settings


def start_run(
    session_id: str,
    mode: str,
    input_text: str,
    model_source_id: str | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    settings = get_effective_settings()
    run_id = str(uuid.uuid4())
    input_hash = hash_text(input_text)
    input_store = None
    if not settings.privacy_mode and settings.allow_query_text_logging:
        input_store = input_text
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO runs (id, session_id, mode, input_hash, input_text, model_source_id, model_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, session_id, mode, input_hash, input_store, model_source_id, model_name),
        )
    return {"id": run_id, "start": time.time()}


def log_run_event(run_id: str, event_type: str, payload: dict[str, Any]) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO run_events (id, run_id, event_type, payload_json) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), run_id, event_type, json.dumps(payload)),
        )


def finish_run(run_id: str, start_time: float) -> None:
    duration_ms = int((time.time() - start_time) * 1000)
    with connection() as conn:
        conn.execute(
            "UPDATE runs SET duration_ms = ? WHERE id = ?",
            (duration_ms, run_id),
        )


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_run(run_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        events = conn.execute(
            "SELECT event_type, payload_json, created_at FROM run_events WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
    result = dict(row)
    result["events"] = [
        {"event_type": e["event_type"], "payload": json.loads(e["payload_json"] or "{}"), "created_at": e["created_at"]}
        for e in events
    ]
    return result
