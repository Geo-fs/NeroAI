"""Policy guard enforces permissions independent from model outputs."""

from __future__ import annotations

from app.models.schemas import PermissionType
from app.services.permission_broker import check_permission
from app.services.path_security import path_within_scopes
from app.services.policy_dsl import evaluate_effect, parse_policy
from app.services.settings_profiles import get_active_profile
from app.services.workspaces import get_active_workspace
from app.services.settings_service import get_effective_settings

MODE_TOOL_ALLOWLIST: dict[str, set[str]] = {
    "chat": {"file_read"},
    "workflow": {"file_read", "file_write", "file_list", "file_read_batch"},
}


def assert_allowed(permission: PermissionType, session_id: str, path: str | None = None, safe_mode: bool = True) -> tuple[bool, str]:
    if safe_mode and permission in {"web.search", "screen.capture", "clipboard.read", "clipboard.write", "process.run"}:
        return False, "Safe mode blocks this permission"
    allowed, reason = check_permission(permission, session_id=session_id, path=path)
    if not allowed:
        return False, reason
    if path:
        workspace = get_active_workspace()
        scopes = workspace.get("scopes", []) if workspace else []
        if scopes:
            ok, workspace_reason = path_within_scopes(path, scopes)
            if not ok:
                settings = get_effective_settings()
                if settings.quarantine_mode:
                    return True, "Quarantine required"
                return False, f"Workspace scope denied: {workspace_reason}"
    return True, "Granted"


def is_tool_allowed_in_mode(tool: str, mode: str) -> tuple[bool, str]:
    allowed = MODE_TOOL_ALLOWLIST.get(mode, set())
    if tool not in allowed:
        return False, f"Tool {tool} is not allowed in mode {mode}"
    return True, "Allowed"


def is_tool_allowed_in_workspace(tool: str) -> tuple[bool, str]:
    workspace = get_active_workspace()
    if not workspace:
        return True, "No workspace constraint"
    allowed_tools = workspace.get("allowed_tools", [])
    if not allowed_tools:
        return True, "No workspace tool allowlist"
    if tool not in allowed_tools:
        return False, f"Tool {tool} not allowed by workspace"
    return True, "Allowed"


def _load_policy_text() -> str:
    profile = get_active_profile()
    workspace = get_active_workspace()
    parts: list[str] = []
    if profile and profile.get("payload", {}).get("policy_rules"):
        parts.append(profile["payload"]["policy_rules"])
    if workspace and workspace.get("settings", {}).get("policy_rules"):
        parts.append(workspace["settings"]["policy_rules"])
    return "\n".join(parts)


def policy_allows_action(action: str, confirmed: bool = False) -> tuple[bool, str]:
    text = _load_policy_text()
    if not text.strip():
        return True, "No policy rules"
    parsed = parse_policy(text)
    if parsed.errors:
        return False, f"Policy parse errors: {parsed.errors[0]}"
    profile = get_active_profile()
    workspace = get_active_workspace()
    profile_name = profile.get("name") if profile else None
    workspace_name = workspace.get("name") if workspace else None
    decision = evaluate_effect(parsed.effects, action, profile_name, workspace_name, confirmed=confirmed)
    if decision == "deny":
        return False, "Policy denied action"
    return True, "Allowed"


def assert_permission(permission: PermissionType, session_id: str, safe_mode: bool, path: str | None = None) -> None:
    allowed, reason = assert_allowed(permission, session_id=session_id, path=path, safe_mode=safe_mode)
    if not allowed:
        raise PermissionError(f"permission_required:{permission}:{reason}")
