from pathlib import Path

from app.plugins.file_write import FileWritePlugin


def test_file_write_preview_requires_confirm(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("old", encoding="utf-8")
    plugin = FileWritePlugin()
    result = plugin.run({"path": str(path), "content": "new"})
    assert result.get("requires_confirmation") is True
