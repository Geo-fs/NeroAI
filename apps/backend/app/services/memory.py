"""Structured memory storage (preferences and project facts)."""

from __future__ import annotations

import uuid
from typing import Any

from app.db.sqlite import connection


def list_memory() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, kind, content, created_at, updated_at FROM memory_items ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def create_memory(kind: str, content: str) -> dict[str, Any]:
    memory_id = str(uuid.uuid4())
    with connection() as conn:
        conn.execute(
            "INSERT INTO memory_items (id, kind, content) VALUES (?, ?, ?)",
            (memory_id, kind, content),
        )
    return get_memory(memory_id)  # type: ignore


def get_memory(memory_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, kind, content, created_at, updated_at FROM memory_items WHERE id = ?",
            (memory_id,),
        ).fetchone()
    return dict(row) if row else None


def update_memory(memory_id: str, content: str) -> dict[str, Any]:
    with connection() as conn:
        conn.execute(
            "UPDATE memory_items SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (content, memory_id),
        )
    return get_memory(memory_id)  # type: ignore


def delete_memory(memory_id: str) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))
