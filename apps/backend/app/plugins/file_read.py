from __future__ import annotations

from pathlib import Path

from app.plugins.base import PermissionRequirement


class FileReadPlugin:
    name = "file_read"
    description = "Read text file content"
    input_schema = {"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}}}
    permission_requirements = [PermissionRequirement(permission="filesystem.read", path_scoped=True)]

    def run(self, payload: dict) -> dict:
        path = Path(payload["path"]).resolve()
        content = path.read_text(encoding="utf-8")
        return {"path": str(path), "content": content[:200000]}
