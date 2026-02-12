from __future__ import annotations

from pathlib import Path
import difflib

from app.plugins.base import PermissionRequirement


class FileWritePlugin:
    name = "file_write"
    description = "Write text file content"
    input_schema = {
        "type": "object",
        "required": ["path", "content"],
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
    }
    permission_requirements = [PermissionRequirement(permission="filesystem.write", path_scoped=True)]

    def run(self, payload: dict) -> dict:
        path = Path(payload["path"]).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        content = payload["content"]
        confirm = bool(payload.get("confirm", False))
        preview_only = bool(payload.get("preview_only", False))
        prior = path.read_text(encoding="utf-8") if path.exists() else ""
        diff = "\n".join(
            difflib.unified_diff(
                prior.splitlines(),
                content.splitlines(),
                fromfile=str(path),
                tofile=str(path),
                lineterm="",
            )
        )
        if payload.get("write_preview_file"):
            preview_path = path.with_suffix(path.suffix + ".neroai.preview")
            preview_path.write_text(content, encoding="utf-8")
            return {"path": str(preview_path), "preview_diff": diff, "requires_confirmation": True}
        if preview_only or (path.exists() and not confirm):
            return {
                "path": str(path),
                "preview_diff": diff,
                "requires_confirmation": True,
            }
        path.write_text(content, encoding="utf-8")
        return {"path": str(path), "written_chars": len(content), "preview_diff": diff }
