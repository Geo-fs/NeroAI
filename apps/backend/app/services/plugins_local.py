"""Local plugin loader from apps/backend/plugins_local."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import uuid
from typing import Any

from app.db.sqlite import connection
from app.plugins.base import ToolPlugin


PLUGINS_LOCAL_DIR = Path(__file__).resolve().parents[2] / "plugins_local"


def _load_module(entrypoint: str):
    spec = importlib.util.spec_from_file_location("neroai_local_plugin", entrypoint)
    if not spec or not spec.loader:
        raise RuntimeError("Failed to load plugin entrypoint")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def load_local_plugins() -> dict[str, ToolPlugin]:
    PLUGINS_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    registry: dict[str, BasePlugin] = {}
    for manifest_path in PLUGINS_LOCAL_DIR.glob("*/manifest.json"):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest_path.parent / data["entrypoint"]
        enabled = data.get("enabled", True)
        if not enabled:
            continue
        module = _load_module(str(entry))
        plugin_obj = getattr(module, "PLUGIN", None)
        if plugin_obj and getattr(plugin_obj, "name", None):
            register_plugin_record(plugin_obj.name, data.get("version", "0.0.0"), str(entry))
            registry[plugin_obj.name] = plugin_obj
    return registry


def list_plugin_records() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM plugin_registry ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def register_plugin_record(name: str, version: str, path: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO plugin_registry (id, name, version, path, enabled) VALUES (?, ?, ?, ?, 1)",
            (str(uuid.uuid4()), name, version, path),
        )


def set_plugin_enabled(plugin_id: str, enabled: bool) -> None:
    with connection() as conn:
        conn.execute("UPDATE plugin_registry SET enabled = ? WHERE id = ?", (1 if enabled else 0, plugin_id))
