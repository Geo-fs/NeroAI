from __future__ import annotations

from pathlib import Path

from app.plugins.base import PermissionRequirement


class FileReadBatchPlugin:
    name = "file_read_batch"
    description = "Read multiple text files with size limits."
    input_schema = {
        "type": "object",
        "required": ["paths"],
        "properties": {"paths": {"type": "array", "items": {"type": "string"}}, "max_chars_per_file": {"type": "integer"}},
    }
    permission_requirements = [PermissionRequirement(permission="filesystem.read", path_scoped=False)]

    def run(self, payload: dict) -> dict:
        max_chars = int(payload.get("max_chars_per_file", 5000))
        result = []
        for raw in payload.get("paths", []):
            path = Path(raw).resolve()
            try:
                content = path.read_text(encoding="utf-8")
                result.append({"path": str(path), "content": content[:max_chars]})
            except Exception as exc:
                result.append({"path": str(path), "error": str(exc)})
        return {"files": result}

