"""Windows firewall hardening helpers for the tool runner."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from app.models.schemas import SecurityLockdownResponse, SecurityPlanResponse, SecurityStatusResponse
from app.services.tool_runner import get_tool_runner_program_path

FIREWALL_RULE_NAME = "NeroAI Tool Runner - Block Outbound"


def _quote_ps(value: str) -> str:
    return value.replace("'", "''")


def build_lockdown_commands(program_path: str) -> dict[str, str]:
    program = str(Path(program_path).resolve())
    delete_rule = f'netsh advfirewall firewall delete rule name="{FIREWALL_RULE_NAME}"'
    add_rule = (
        f'netsh advfirewall firewall add rule name="{FIREWALL_RULE_NAME}" '
        f'dir=out action=block program="{program}" enable=yes profile=any'
    )
    status = (
        "Get-NetFirewallRule -DisplayName '" + _quote_ps(FIREWALL_RULE_NAME) + "' "
        "-ErrorAction SilentlyContinue | ConvertTo-Json -Depth 4"
    )
    return {
        "delete_rule_command": delete_rule,
        "add_rule_command": add_rule,
        "status_check_command": status,
    }


def get_security_plan() -> SecurityPlanResponse:
    program = get_tool_runner_program_path()
    cmds = build_lockdown_commands(program)
    return SecurityPlanResponse(
        rule_name=FIREWALL_RULE_NAME,
        tool_runner_program=program,
        create_rule_command=f"{cmds['delete_rule_command']} && {cmds['add_rule_command']}",
        status_check_command=cmds["status_check_command"],
    )


def launch_lockdown_with_uac() -> SecurityLockdownResponse:
    plan = get_security_plan()
    cmds = build_lockdown_commands(plan.tool_runner_program)
    elevated_inner = (
        cmds["delete_rule_command"] + " | Out-Null; " + cmds["add_rule_command"] + " | Out-Null"
    )
    script = (
        "Start-Process -FilePath 'powershell.exe' -Verb RunAs "
        "-ArgumentList @('-NoProfile','-Command','" + _quote_ps(elevated_inner) + "')"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-Command", script])
        return SecurityLockdownResponse(launched=True, detail="UAC prompt launched. Approve to apply firewall rule.")
    except Exception as exc:
        return SecurityLockdownResponse(launched=False, detail=f"Failed to launch UAC request: {exc}")


def get_lockdown_status() -> SecurityStatusResponse:
    plan = get_security_plan()
    ps = (
        "$r = Get-NetFirewallRule -DisplayName '" + _quote_ps(FIREWALL_RULE_NAME) + "' -ErrorAction SilentlyContinue; "
        "if (-not $r) { "
        "  [PSCustomObject]@{exists=$false;enabled=$false;outbound_block=$false;program='';detail='Rule not found'} | ConvertTo-Json -Compress; exit 0 "
        "} "
        "$app = Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $r | Select-Object -First 1; "
        "[PSCustomObject]@{"
        "exists=$true;"
        "enabled=($r.Enabled -eq 'True');"
        "outbound_block=($r.Direction -eq 'Outbound' -and $r.Action -eq 'Block');"
        "program=($app.Program);"
        "detail='Rule found'"
        "} | ConvertTo-Json -Compress"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return SecurityStatusResponse(
                rule_name=plan.rule_name,
                tool_runner_program=plan.tool_runner_program,
                exists=False,
                enabled=False,
                outbound_block=False,
                program_matches=False,
                confirmed_blocking=False,
                detail=(proc.stderr or "Failed to query firewall rule").strip(),
            )
        data = json.loads(proc.stdout.strip())
        program = str(Path(data.get("program", "")).resolve()) if data.get("program") else ""
        expected = str(Path(plan.tool_runner_program).resolve())
        program_matches = program.lower() == expected.lower()
        exists = bool(data.get("exists", False))
        enabled = bool(data.get("enabled", False))
        outbound_block = bool(data.get("outbound_block", False))
        confirmed = exists and enabled and outbound_block and program_matches
        return SecurityStatusResponse(
            rule_name=plan.rule_name,
            tool_runner_program=plan.tool_runner_program,
            exists=exists,
            enabled=enabled,
            outbound_block=outbound_block,
            program_matches=program_matches,
            confirmed_blocking=confirmed,
            detail=data.get("detail", ""),
        )
    except Exception as exc:
        return SecurityStatusResponse(
            rule_name=plan.rule_name,
            tool_runner_program=plan.tool_runner_program,
            exists=False,
            enabled=False,
            outbound_block=False,
            program_matches=False,
            confirmed_blocking=False,
            detail=f"Status check failed: {exc}",
        )
