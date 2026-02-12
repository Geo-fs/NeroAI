"""Application settings persistence and privacy policy helpers."""

from __future__ import annotations

import json
from typing import Any

from app.db.sqlite import connection
from app.models.schemas import SettingsResponse, SettingsUpdateRequest
from app.services.settings_registry import (
    enforce_safe_defaults,
    registry_defaults,
    validate_payload,
)
from app.services.workspaces import get_active_workspace

DEFAULTS = registry_defaults()


def get_settings() -> SettingsResponse:
    merged = dict(DEFAULTS)
    with connection() as conn:
        rows = conn.execute("SELECT key, value_json FROM app_settings").fetchall()
    for row in rows:
        merged[row["key"]] = json.loads(row["value_json"])
    merged = enforce_safe_defaults(validate_payload(merged))
    return SettingsResponse(**merged)


def update_settings(payload: SettingsUpdateRequest) -> SettingsResponse:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return get_settings()
    updates = enforce_safe_defaults(validate_payload({**get_settings().model_dump(), **updates}))
    with connection() as conn:
        for key, value in updates.items():
            conn.execute(
                """
                INSERT INTO app_settings (key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=CURRENT_TIMESTAMP
                """,
                (key, json.dumps(value)),
            )
    return get_settings()


def get_setting(key: str, default: Any) -> Any:
    settings = get_settings().model_dump()
    return settings.get(key, default)


def get_effective_settings() -> SettingsResponse:
    """Merge app settings with active workspace overrides."""
    base = get_settings().model_dump()
    workspace = get_active_workspace()
    if workspace and workspace.get("settings"):
        merged = dict(base)
        merged.update(workspace["settings"])
        merged = enforce_safe_defaults(validate_payload(merged))
        return SettingsResponse(**merged)
    return SettingsResponse(**base)
