"""Run limits and budgets enforcement."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from app.services.policy_dsl import apply_limit_overrides, parse_policy
from app.services.settings_profiles import get_active_profile
from app.services.workspaces import get_active_workspace


@dataclass
class RunLimiter:
    max_tool_calls_per_message: int
    max_tool_calls_per_minute: int
    max_files_read_per_run: int
    max_bytes_read_per_run: int
    max_runtime_seconds: int
    session_id: str
    start_time: float = field(default_factory=time.time)
    tool_calls: int = 0
    files_read: int = 0
    bytes_read: int = 0

    def check_runtime(self) -> None:
        if time.time() - self.start_time > self.max_runtime_seconds:
            raise RuntimeError("Run time limit exceeded")

    def check_tool_call(self) -> None:
        if self.tool_calls + 1 > self.max_tool_calls_per_message:
            raise RuntimeError("Tool call limit exceeded for this message")

    def record_tool_call(self) -> None:
        self.tool_calls += 1

    def record_file_reads(self, files: int, bytes_read: int) -> None:
        if self.files_read + files > self.max_files_read_per_run:
            raise RuntimeError("File read count limit exceeded")
        if self.bytes_read + bytes_read > self.max_bytes_read_per_run:
            raise RuntimeError("File read bytes limit exceeded")
        self.files_read += files
        self.bytes_read += bytes_read


_CALL_WINDOW: dict[str, deque[float]] = {}


def enforce_rate_limit(session_id: str, max_per_minute: int) -> None:
    now = time.time()
    window = _CALL_WINDOW.setdefault(session_id, deque())
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) + 1 > max_per_minute:
        raise RuntimeError("Tool call rate limit exceeded")
    window.append(now)


def build_run_limiter(settings: dict[str, int], session_id: str) -> RunLimiter:
    profile = get_active_profile()
    workspace = get_active_workspace()
    profile_name = profile.get("name") if profile else None
    workspace_name = workspace.get("name") if workspace else None
    policy_text = ""
    if profile and profile.get("payload", {}).get("policy_rules"):
        policy_text += profile["payload"]["policy_rules"] + "\n"
    if workspace and workspace.get("settings", {}).get("policy_rules"):
        policy_text += workspace["settings"]["policy_rules"] + "\n"
    parsed = parse_policy(policy_text) if policy_text.strip() else None
    limits = dict(settings)
    if parsed and not parsed.errors:
        limits = apply_limit_overrides(limits, parsed.limits, profile_name, workspace_name, confirmed=False)
    return RunLimiter(
        max_tool_calls_per_message=limits["max_tool_calls_per_message"],
        max_tool_calls_per_minute=limits["max_tool_calls_per_minute"],
        max_files_read_per_run=limits["max_files_read_per_run"],
        max_bytes_read_per_run=limits["max_bytes_read_per_run"],
        max_runtime_seconds=limits["max_runtime_seconds"],
        session_id=session_id,
    )
