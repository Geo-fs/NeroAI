from pathlib import Path

from app.services import security_hardening
from app.services.tool_runner import get_tool_runner_program_path


def test_tool_runner_program_path_detection(monkeypatch) -> None:
    fake = str(Path("C:/Tools/Python/python.exe"))
    monkeypatch.setattr("app.services.tool_runner.sys.executable", fake)
    resolved = get_tool_runner_program_path()
    assert resolved.lower().endswith("python.exe")


def test_firewall_command_generation_contains_rule_and_program() -> None:
    path = r"C:\Users\mike\OneDrive\Desktop\AIs.etc\NeroAI\apps\backend\.venv\Scripts\python.exe"
    cmds = security_hardening.build_lockdown_commands(path)
    assert security_hardening.FIREWALL_RULE_NAME in cmds["add_rule_command"]
    assert 'dir=out' in cmds["add_rule_command"]
    assert 'action=block' in cmds["add_rule_command"]
    assert f'program="{str(Path(path).resolve())}"' in cmds["add_rule_command"]

