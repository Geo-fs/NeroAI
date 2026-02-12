"""Settings profiles using normalized tables with history snapshots."""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.sqlite import connection
from app.services.settings_registry import enforce_safe_defaults, registry_defaults, validate_payload


HISTORY_LIMIT = 10


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Profile payload must be an object")
    merged = dict(registry_defaults())
    merged.update(payload)
    merged = validate_payload(merged)
    merged = enforce_safe_defaults(merged)
    return merged


def list_profiles() -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, name, version, created_at, updated_at, is_default, is_active FROM profiles ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_profile(profile_id: str) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, name, version, created_at, updated_at, is_default, is_active FROM profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()
        if not row:
            return None
        settings = conn.execute(
            "SELECT key, value_json FROM profile_settings WHERE profile_id = ?",
            (profile_id,),
        ).fetchall()
    payload = {r["key"]: json.loads(r["value_json"]) for r in settings}
    return {**dict(row), "payload": payload}


def get_active_profile() -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT id FROM profiles WHERE is_active = 1").fetchone()
    if not row:
        return None
    return get_profile(row["id"])


def _snapshot_profile(profile_id: str, payload: dict[str, Any] | None = None) -> None:
    profile = get_profile(profile_id)
    if not profile:
        return
    snapshot = payload if payload is not None else profile["payload"]
    with connection() as conn:
        conn.execute(
            "INSERT INTO profile_history (id, profile_id, snapshot_json) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), profile_id, json.dumps(snapshot)),
        )
        rows = conn.execute(
            "SELECT id FROM profile_history WHERE profile_id = ? ORDER BY created_at DESC",
            (profile_id,),
        ).fetchall()
        if len(rows) > HISTORY_LIMIT:
            for row in rows[HISTORY_LIMIT:]:
                conn.execute("DELETE FROM profile_history WHERE id = ?", (row["id"],))


def create_profile(name: str, payload: dict[str, Any] | None = None) -> dict:
    profile_id = str(uuid.uuid4())
    normalized = _normalize_payload(payload or {})
    with connection() as conn:
        conn.execute(
            "INSERT INTO profiles (id, name, version, is_default, is_active) VALUES (?, ?, 1, 0, 0)",
            (profile_id, name),
        )
        for key, value in normalized.items():
            conn.execute(
                "INSERT INTO profile_settings (profile_id, key, value_json) VALUES (?, ?, ?)",
                (profile_id, key, json.dumps(value)),
            )
    _snapshot_profile(profile_id, normalized)
    return get_profile(profile_id)  # type: ignore


def update_profile(profile_id: str, payload: dict[str, Any], name: str | None = None) -> dict:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")
    _snapshot_profile(profile_id, profile["payload"])
    normalized = _normalize_payload(payload)
    with connection() as conn:
        if name:
            conn.execute(
                "UPDATE profiles SET name = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, profile_id),
            )
        else:
            conn.execute(
                "UPDATE profiles SET version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (profile_id,),
            )
        for key, value in normalized.items():
            conn.execute(
                "INSERT OR REPLACE INTO profile_settings (profile_id, key, value_json) VALUES (?, ?, ?)",
                (profile_id, key, json.dumps(value)),
            )
    return get_profile(profile_id)  # type: ignore


def duplicate_profile(profile_id: str, new_name: str) -> dict:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")
    return create_profile(new_name, profile["payload"])


def delete_profile(profile_id: str) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM profile_history WHERE profile_id = ?", (profile_id,))
        conn.execute("DELETE FROM profile_settings WHERE profile_id = ?", (profile_id,))
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))


def export_profile(profile_id: str) -> dict:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")
    return {
        "id": profile["id"],
        "name": profile["name"],
        "version": profile.get("version", 1),
        "payload": profile["payload"],
    }


def import_profile(payload: dict[str, Any]) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Import payload must be an object")
    name = payload.get("name") or "Imported Profile"
    body = payload.get("payload") or {}
    if not isinstance(body, dict):
        raise ValueError("Profile payload must be an object")
    return create_profile(name, body)


def activate_profile(profile_id: str) -> dict:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")
    with connection() as conn:
        conn.execute("UPDATE profiles SET is_active = 0 WHERE is_active = 1")
        conn.execute("UPDATE profiles SET is_active = 1 WHERE id = ?", (profile_id,))
        # Apply profile settings to global app_settings for effective defaults.
        for key, value in profile["payload"].items():
            conn.execute(
                """
                INSERT INTO app_settings (key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=CURRENT_TIMESTAMP
                """,
                (key, json.dumps(value)),
            )
    return get_profile(profile_id)  # type: ignore


def rollback_profile(profile_id: str) -> dict:
    with connection() as conn:
        row = conn.execute(
            "SELECT snapshot_json FROM profile_history WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
            (profile_id,),
        ).fetchone()
    if not row:
        raise ValueError("No history found")
    payload = json.loads(row["snapshot_json"])
    return update_profile(profile_id, payload)


def reset_category(profile_id: str, keys: list[str]) -> dict:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")
    defaults = registry_defaults()
    payload = dict(profile["payload"])
    for key in keys:
        if key in defaults:
            payload[key] = defaults[key]
    return update_profile(profile_id, payload)
