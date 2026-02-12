"""Clipboard helpers for Windows with permission gating at route layer."""

from __future__ import annotations

import subprocess


def read_clipboard() -> str:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "Failed to read clipboard").strip())
    return proc.stdout


def write_clipboard(text: str) -> None:
    escaped = text.replace("'", "''")
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value '{escaped}'"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "Failed to write clipboard").strip())
