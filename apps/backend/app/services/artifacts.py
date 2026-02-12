"""Artifacts library for saving outputs."""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.sqlite import connection


def create_artifact(
    name: str,
    content: str,
    artifact_type: str,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = str(uuid.uuid4())
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO artifacts (id, run_id, type, name, content, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (artifact_id, run_id, artifact_type, name, content, json.dumps(metadata or {})),
        )
    return get_artifact(artifact_id)  # type: ignore


def list_artifacts(limit: int = 100) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        result.append(item)
    return result


def get_artifact(artifact_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    return item


def delete_artifact(artifact_id: str) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
