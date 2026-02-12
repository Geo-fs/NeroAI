"""Permission broker with default-deny grants and strict path scopes."""

from __future__ import annotations

import json
import uuid

from app.db.sqlite import connection
from app.models.schemas import GrantPermissionRequest, PermissionGrantResponse, PermissionType
from app.services.audit import log_event
from app.services.path_security import normalize_path, path_within_scopes


def grant_permission(payload: GrantPermissionRequest, session_id: str) -> None:
    session_value = None if payload.scope == "always" else session_id
    scopes = [str(normalize_path(p)) for p in payload.allowed_paths]
    with connection() as conn:
        conn.execute(
            "DELETE FROM permission_grants WHERE permission = ? AND (session_id = ? OR session_id IS NULL)",
            (payload.permission, session_id),
        )
        conn.execute(
            "INSERT INTO permission_grants (id, permission, scope, session_id, allowed_paths_json) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), payload.permission, payload.scope, session_value, json.dumps(scopes)),
        )
    log_event(
        "permission.grant",
        f"Granted {payload.permission} with scope {payload.scope}",
        {"permission": payload.permission, "scope": payload.scope},
        session_id=session_id,
    )


def _select_grant(permission: PermissionType, session_id: str) -> dict | None:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT permission, scope, session_id, allowed_paths_json
            FROM permission_grants
            WHERE permission = ? AND (session_id = ? OR session_id IS NULL)
            """,
            (permission, session_id),
        ).fetchall()
    if not rows:
        return None
    selected = sorted(rows, key=lambda row: 0 if row["session_id"] == session_id else 1)[0]
    return dict(selected)


def check_permission(permission: PermissionType, session_id: str, path: str | None = None) -> tuple[bool, str]:
    selected = _select_grant(permission, session_id)
    if not selected:
        return False, "No grant found"

    scopes = json.loads(selected["allowed_paths_json"] or "[]")
    if path:
        ok, reason = path_within_scopes(path, scopes)
        if not ok:
            return False, reason

    if selected["scope"] == "once":
        with connection() as conn:
            conn.execute(
                "DELETE FROM permission_grants WHERE permission = ? AND scope = 'once' AND session_id = ?",
                (permission, session_id),
            )
    return True, "Granted"


def revoke_permission(permission: str, session_id: str) -> None:
    with connection() as conn:
        conn.execute(
            "DELETE FROM permission_grants WHERE permission = ? AND (session_id = ? OR session_id IS NULL)",
            (permission, session_id),
        )
    log_event("permission.revoke", f"Revoked {permission}", {"permission": permission}, session_id=session_id)


def list_grants(session_id: str) -> list[PermissionGrantResponse]:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT permission, scope, session_id, allowed_paths_json
            FROM permission_grants WHERE session_id = ? OR session_id IS NULL
            """,
            (session_id,),
        ).fetchall()
    results: list[PermissionGrantResponse] = []
    for row in rows:
        item = dict(row)
        results.append(
            PermissionGrantResponse(
                permission=item["permission"],
                scope=item["scope"],
                session_id=item["session_id"],
                allowed_paths=json.loads(item["allowed_paths_json"] or "[]"),
            )
        )
    return results


__all__ = ["grant_permission", "check_permission", "revoke_permission", "list_grants", "path_within_scopes"]

