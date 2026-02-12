"""Plugin listing and enable/disable for UI."""

from __future__ import annotations

from typing import Any

from app.db.sqlite import connection
from app.plugins.registry import PLUGIN_REGISTRY


def list_plugins() -> list[dict[str, Any]]:
    builtins = [{"name": name, "type": "builtin", "enabled": True} for name in PLUGIN_REGISTRY.keys()]
    with connection() as conn:
        rows = conn.execute("SELECT id, name, version, path, enabled FROM plugin_registry").fetchall()
    locals_ = [
        {"id": r["id"], "name": r["name"], "version": r["version"], "path": r["path"], "type": "local", "enabled": bool(r["enabled"])}
        for r in rows
    ]
    return builtins + locals_


def set_plugin_enabled(plugin_id: str, enabled: bool) -> None:
    with connection() as conn:
        conn.execute("UPDATE plugin_registry SET enabled = ? WHERE id = ?", (1 if enabled else 0, plugin_id))
