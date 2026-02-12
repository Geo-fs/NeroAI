"""Workspace management and scoped policies."""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.sqlite import connection
from app.services.settings_profiles import activate_profile
from app.services.settings_registry import enforce_safe_defaults, registry_defaults, validate_payload


def list_workspaces() -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, default_profile_id, default_model_source_id, default_model,
                   logging_strictness, is_active, created_at, updated_at
            FROM workspaces
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_workspace(workspace_id: str) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, description, default_profile_id, default_model_source_id, default_model,
                   logging_strictness, is_active, created_at, updated_at
            FROM workspaces WHERE id = ?
            """,
            (workspace_id,),
        ).fetchone()
        if not row:
            return None
        scopes = conn.execute(
            "SELECT path FROM workspace_scopes WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchall()
        tools = conn.execute(
            "SELECT tool_name FROM workspace_tools WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchall()
        settings = conn.execute(
            "SELECT key, value_json FROM workspace_settings WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchall()
    payload = {s["key"]: json.loads(s["value_json"]) for s in settings}
    return {
        **dict(row),
        "scopes": [s["path"] for s in scopes],
        "allowed_tools": [t["tool_name"] for t in tools],
        "settings": payload,
    }


def get_active_workspace() -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT id FROM workspaces WHERE is_active = 1").fetchone()
    if not row:
        return None
    return get_workspace(row["id"])


def _normalize_settings(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Workspace settings must be an object")
    merged = dict(registry_defaults())
    merged.update(payload)
    merged = validate_payload(merged)
    merged = enforce_safe_defaults(merged)
    return merged


def create_workspace(
    name: str,
    description: str = "",
    scopes: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    settings: dict[str, Any] | None = None,
    default_profile_id: str | None = None,
    default_model_source_id: str | None = None,
    default_model: str | None = None,
    logging_strictness: str = "standard",
) -> dict:
    workspace_id = str(uuid.uuid4())
    normalized = _normalize_settings(settings or {})
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO workspaces (id, name, description, default_profile_id, default_model_source_id, default_model, logging_strictness, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (workspace_id, name, description, default_profile_id, default_model_source_id, default_model, logging_strictness),
        )
        for path in scopes or []:
            conn.execute(
                "INSERT INTO workspace_scopes (id, workspace_id, path) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), workspace_id, path),
            )
        for tool in allowed_tools or []:
            conn.execute(
                "INSERT INTO workspace_tools (id, workspace_id, tool_name) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), workspace_id, tool),
            )
        for key, value in normalized.items():
            if settings and key not in settings:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO workspace_settings (workspace_id, key, value_json) VALUES (?, ?, ?)",
                (workspace_id, key, json.dumps(value)),
            )
    return get_workspace(workspace_id)  # type: ignore


def update_workspace(
    workspace_id: str,
    name: str | None = None,
    description: str | None = None,
    scopes: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    settings: dict[str, Any] | None = None,
    default_profile_id: str | None = None,
    default_model_source_id: str | None = None,
    default_model: str | None = None,
    logging_strictness: str | None = None,
) -> dict:
    workspace = get_workspace(workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    normalized = _normalize_settings(settings or {}) if settings is not None else None
    with connection() as conn:
        if name is not None or description is not None or default_profile_id is not None or default_model_source_id is not None or default_model is not None or logging_strictness is not None:
            conn.execute(
                """
                UPDATE workspaces
                SET name = COALESCE(?, name),
                    description = COALESCE(?, description),
                    default_profile_id = COALESCE(?, default_profile_id),
                    default_model_source_id = COALESCE(?, default_model_source_id),
                    default_model = COALESCE(?, default_model),
                    logging_strictness = COALESCE(?, logging_strictness),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, description, default_profile_id, default_model_source_id, default_model, logging_strictness, workspace_id),
            )
        if scopes is not None:
            conn.execute("DELETE FROM workspace_scopes WHERE workspace_id = ?", (workspace_id,))
            for path in scopes:
                conn.execute(
                    "INSERT INTO workspace_scopes (id, workspace_id, path) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), workspace_id, path),
                )
        if allowed_tools is not None:
            conn.execute("DELETE FROM workspace_tools WHERE workspace_id = ?", (workspace_id,))
            for tool in allowed_tools:
                conn.execute(
                    "INSERT INTO workspace_tools (id, workspace_id, tool_name) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), workspace_id, tool),
                )
        if normalized is not None:
            conn.execute("DELETE FROM workspace_settings WHERE workspace_id = ?", (workspace_id,))
            for key, value in normalized.items():
                if settings and key not in settings:
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO workspace_settings (workspace_id, key, value_json) VALUES (?, ?, ?)",
                    (workspace_id, key, json.dumps(value)),
                )
    return get_workspace(workspace_id)  # type: ignore


def delete_workspace(workspace_id: str) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM workspace_scopes WHERE workspace_id = ?", (workspace_id,))
        conn.execute("DELETE FROM workspace_tools WHERE workspace_id = ?", (workspace_id,))
        conn.execute("DELETE FROM workspace_settings WHERE workspace_id = ?", (workspace_id,))
        conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))


def activate_workspace(workspace_id: str) -> dict:
    workspace = get_workspace(workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    with connection() as conn:
        conn.execute("UPDATE workspaces SET is_active = 0 WHERE is_active = 1")
        conn.execute("UPDATE workspaces SET is_active = 1 WHERE id = ?", (workspace_id,))
    if workspace.get("default_profile_id"):
        try:
            activate_profile(workspace["default_profile_id"])
        except Exception:
            pass
    return get_workspace(workspace_id)  # type: ignore


__all__ = [
    "list_workspaces",
    "get_workspace",
    "get_active_workspace",
    "create_workspace",
    "update_workspace",
    "delete_workspace",
    "activate_workspace",
]
