from __future__ import annotations

from pathlib import Path

from app.plugins.base import PermissionRequirement


class FileListPlugin:
    name = "file_list"
    description = "List text files in a folder."
    input_schema = {
        "type": "object",
        "required": ["path"],
        "properties": {"path": {"type": "string"}, "max_files": {"type": "integer"}},
    }
    permission_requirements = [PermissionRequirement(permission="filesystem.read", path_scoped=True)]

    def run(self, payload: dict) -> dict:
        base = Path(payload["path"]).resolve()
        max_files = int(payload.get("max_files", 25))
        exts = {".txt", ".md", ".py", ".json", ".yaml", ".yml", ".csv", ".log"}
        files: list[str] = []
        for item in base.rglob("*"):
            if item.is_file() and item.suffix.lower() in exts:
                files.append(str(item))
            if len(files) >= max_files:
                break
        return {"path": str(base), "files": files}

