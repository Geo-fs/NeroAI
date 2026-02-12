from pathlib import Path

import pytest

from app.models.schemas import GrantPermissionRequest
from app.services.path_security import path_within_scopes
from app.services.permission_broker import check_permission, grant_permission


def test_path_traversal_rejected(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside" / "x.txt"
    outside.parent.mkdir()
    outside.write_text("x", encoding="utf-8")
    ok, _ = path_within_scopes(str(base / ".." / "outside" / "x.txt"), [str(base)])
    assert ok is False


def test_once_permission_consumed(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    target = base / "a.txt"
    target.write_text("hello", encoding="utf-8")
    grant_permission(
        GrantPermissionRequest(permission="filesystem.read", scope="once", allowed_paths=[str(base)]),
        session_id="test-session",
    )
    first = check_permission("filesystem.read", session_id="test-session", path=str(target))
    second = check_permission("filesystem.read", session_id="test-session", path=str(target))
    assert first[0] is True
    assert second[0] is False


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    base = tmp_path / "scope"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target.txt").write_text("x", encoding="utf-8")
    link = base / "link.txt"
    try:
        link.symlink_to(outside / "target.txt")
    except OSError:
        pytest.skip("Symlink creation not permitted in this environment")

    ok, _ = path_within_scopes(str(link), [str(base)])
    assert ok is False
