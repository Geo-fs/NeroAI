"""Hardened tool runner using subprocess boundaries and strict policy."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from app.db.sqlite import DATA_DIR
from app.plugins.registry import PLUGIN_REGISTRY
from app.services.audit import log_event
from app.services.path_security import path_within_scopes
from app.services.permission_broker import list_grants
from app.services.limits import RunLimiter, enforce_rate_limit
from app.services.policy_guard import assert_allowed, is_tool_allowed_in_mode, is_tool_allowed_in_workspace, policy_allows_action
from app.services.settings_service import get_effective_settings
from app.services.workspaces import get_active_workspace

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_OUTPUT_LIMIT_BYTES = 262_144
TOOL_RUN_DIR = DATA_DIR / "tool_runs"
QUARANTINE_DIR = DATA_DIR / "quarantine"


def _apply_quarantine(paths: list[str], session_id: str) -> list[str]:
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    session_dir = QUARANTINE_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    resolved: list[str] = []
    for item in paths:
        src = Path(item).resolve()
        dest = session_dir / f"{src.name}"
        try:
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            resolved.append(str(dest))
        except Exception:
            resolved.append(item)
    return resolved


def get_tool_runner_program_path() -> str:
    """Return the executable path used to run the tool worker subprocess."""
    return str(Path(sys.executable).resolve())


def _truncate_output(value: str, max_bytes: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return value, False
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n<truncated>", True


def _safe_env() -> dict[str, str]:
    keep = {}
    for key in ("SYSTEMROOT", "COMSPEC", "WINDIR", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            keep[key] = value
    keep["PYTHONIOENCODING"] = "utf-8"
    return keep


def _validate_path_args(tool: str, args: dict[str, Any], session_id: str) -> None:
    grants = {g.permission: g.allowed_paths for g in list_grants(session_id)}
    read_scopes = grants.get("filesystem.read", [])
    write_scopes = grants.get("filesystem.write", [])

    paths = []
    if "path" in args and isinstance(args["path"], str):
        paths.append(args["path"])
    if "paths" in args and isinstance(args["paths"], list):
        paths.extend([p for p in args["paths"] if isinstance(p, str)])

    if tool in {"file_read", "file_list", "file_read_batch"}:
        for item in paths:
            ok, reason = path_within_scopes(item, read_scopes)
            if not ok:
                raise PermissionError(f"permission_required:filesystem.read:{reason}")
    if tool == "file_write":
        for item in paths:
            ok, reason = path_within_scopes(item, write_scopes)
            if not ok:
                raise PermissionError(f"permission_required:filesystem.write:{reason}")


def run_tool(
    tool: str,
    args: dict[str, Any],
    session_id: str,
    safe_mode: bool = True,
    mode: str = "chat",
    limiter: RunLimiter | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    plugin = PLUGIN_REGISTRY.get(tool)
    if not plugin:
        raise ValueError(f"Unknown tool: {tool}")

    mode_ok, mode_reason = is_tool_allowed_in_mode(tool, mode)
    if not mode_ok:
        raise PermissionError(f"permission_required:mode:{mode_reason}")
    workspace_ok, workspace_reason = is_tool_allowed_in_workspace(tool)
    if not workspace_ok:
        raise PermissionError(f"permission_required:workspace:{workspace_reason}")
    policy_ok, policy_reason = policy_allows_action(f"tool.{tool}")
    if not policy_ok:
        log_event(
            "policy.denied",
            f"Policy denied tool {tool}",
            {"tool": tool, "reason": policy_reason},
            session_id=session_id,
        )
        raise PermissionError(f"permission_required:policy:{policy_reason}")

    for req in plugin.permission_requirements:
        path = args.get("path") if req.path_scoped else None
        allowed, reason = assert_allowed(req.permission, session_id=session_id, path=path, safe_mode=safe_mode)
        if not allowed:
            log_event(
                "permission.denied",
                f"Denied {req.permission} for tool {tool}: {reason}",
                {"tool": tool, "permission": req.permission, "reason": reason},
                session_id=session_id,
            )
            raise PermissionError(f"permission_required:{req.permission}:{reason}")

    _validate_path_args(tool, args, session_id=session_id)
    settings = get_effective_settings()
    timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    output_limit = DEFAULT_OUTPUT_LIMIT_BYTES

    if tool == "file_write" and settings.write_preview_default and not args.get("confirm"):
        args = dict(args)
        args["preview_only"] = True

    if tool in {"file_read", "file_read_batch"} and settings.quarantine_mode:
        workspace = get_active_workspace()
        scopes = workspace.get("scopes", []) if workspace else []
        if scopes:
            paths = []
            if tool == "file_read":
                paths = [args.get("path")] if isinstance(args.get("path"), str) else []
            else:
                paths = [p for p in args.get("paths", []) if isinstance(p, str)]
            outside = [p for p in paths if not path_within_scopes(p, scopes)[0]]
            if outside:
                quarantined = _apply_quarantine(paths, session_id=session_id)
                args = dict(args)
                if tool == "file_read":
                    args["path"] = quarantined[0] if quarantined else args.get("path")
                else:
                    args["paths"] = quarantined

    if limiter:
        try:
            limiter.check_runtime()
            limiter.check_tool_call()
            enforce_rate_limit(session_id, limiter.max_tool_calls_per_minute)
            limiter.record_tool_call()
        except RuntimeError as exc:
            log_event(
                "limit.blocked",
                f"Tool {tool} blocked by limits",
                {"tool": tool, "reason": str(exc)},
                session_id=session_id,
            )
            raise

    TOOL_RUN_DIR.mkdir(parents=True, exist_ok=True)
    workdir = TOOL_RUN_DIR / session_id
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        proc = subprocess.run(
            [get_tool_runner_program_path(), "-m", "app.services.tool_worker"],
            input=json.dumps({"tool": tool, "args": args}),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
            cwd=str(workdir),
            env=_safe_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Tool timed out after {timeout_seconds}s") from exc

    stdout, stdout_trunc = _truncate_output(proc.stdout or "", output_limit)
    stderr, stderr_trunc = _truncate_output(proc.stderr or "", output_limit)

    if proc.returncode != 0:
        detail = stderr or stdout or "Tool worker failed"
        raise RuntimeError(detail)

    parsed = json.loads(stdout)
    if not parsed.get("ok", False):
        raise RuntimeError(parsed.get("error", "Tool worker failed"))

    result = parsed["result"]
    if limiter and tool == "file_read":
        content = result.get("content", "")
        limiter.record_file_reads(1, len(str(content).encode("utf-8", errors="ignore")))
    if limiter and tool == "file_read_batch":
        items = result.get("items", [])
        total_bytes = sum(len(str(item.get("content", "")).encode("utf-8", errors="ignore")) for item in items if isinstance(item, dict))
        limiter.record_file_reads(len(items), total_bytes)
    digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode("utf-8")).hexdigest()
    payload: dict[str, Any] = {"tool": tool, "result_hash": digest, "stdout_truncated": stdout_trunc, "stderr_truncated": stderr_trunc}
    if settings.verbose_logging:
        payload["args_sample"] = str(args)[:300]
        payload["result_sample"] = str(result)[:600]
    log_event("tool.call", f"Tool {tool} executed", payload, session_id=session_id)
    if run_id:
        from app.services.run_logger import log_run_event
        log_run_event(run_id, "tool.call", payload)
    return result
