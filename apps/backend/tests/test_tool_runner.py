import json
import subprocess
from pathlib import Path

import pytest

from app.models.schemas import GrantPermissionRequest
from app.services.permission_broker import grant_permission
from app.services.tool_runner import _truncate_output, run_tool


def test_output_truncation() -> None:
    text = "a" * 1000
    truncated, did = _truncate_output(text, 100)
    assert did is True
    assert "<truncated>" in truncated


def test_timeout_enforced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    grant_permission(
        GrantPermissionRequest(permission="filesystem.read", scope="session", allowed_paths=[str(tmp_path)]),
        session_id="t1",
    )

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="python", timeout=30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="timed out"):
        run_tool("file_read", {"path": str(tmp_path / "x.txt")}, session_id="t1", safe_mode=False, mode="workflow")
