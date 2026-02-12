from app.services.permission_broker import grant_permission
from app.models.schemas import GrantPermissionRequest
from app.services.policy_guard import assert_allowed
from app.services.workspaces import activate_workspace, create_workspace, delete_workspace, list_workspaces, update_workspace


def test_workspace_scope_denies_outside_path() -> None:
    ws = create_workspace(name="Test", scopes=["C:/Allowed"])
    activate_workspace(ws["id"])
    grant_permission(
        GrantPermissionRequest(permission="filesystem.read", scope="session", allowed_paths=["C:/"]),
        session_id="s1",
    )
    ok, _ = assert_allowed("filesystem.read", session_id="s1", path="C:/Allowed/file.txt", safe_mode=False)
    assert ok is True
    ok2, reason2 = assert_allowed("filesystem.read", session_id="s1", path="C:/Denied/file.txt", safe_mode=False)
    assert ok2 is True
    assert "Quarantine" in reason2


def test_workspace_crud() -> None:
    ws = create_workspace(name="W1", scopes=["C:/X"], allowed_tools=["file_read"])
    updated = update_workspace(ws["id"], name="W2", scopes=["C:/Y"])
    assert updated["name"] == "W2"
    assert "C:/Y" in updated["scopes"]
    assert len(list_workspaces()) >= 1
    delete_workspace(ws["id"])
