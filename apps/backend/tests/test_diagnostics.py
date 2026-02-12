from pathlib import Path

from app.services.diagnostics import export_diagnostics


def test_export_diagnostics(tmp_path: Path) -> None:
    path = export_diagnostics()
    assert Path(path).exists()
