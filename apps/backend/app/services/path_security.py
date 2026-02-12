"""Path normalization and scope safety checks for Windows-friendly security."""

from __future__ import annotations

import os
import stat
from pathlib import Path


def normalize_path(value: str) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def _is_reparse_point(path: Path) -> bool:
    try:
        attrs = os.lstat(path).st_file_attributes  # type: ignore[attr-defined]
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False


def _nearest_existing(path: Path) -> Path:
    cur = path
    while not cur.exists() and cur.parent != cur:
        cur = cur.parent
    return cur


def path_within_scopes(target_raw: str, scopes: list[str]) -> tuple[bool, str]:
    if not scopes:
        return True, "Scope not required"

    target = normalize_path(target_raw)
    for scope_raw in scopes:
        scope = normalize_path(scope_raw)
        if target == scope or scope in target.parents:
            # Prevent reparse point escapes inside selected scope.
            current = _nearest_existing(target)
            while current != scope and scope in current.parents:
                if _is_reparse_point(current):
                    return False, "Path contains a reparse point/junction"
                current = current.parent
            return True, "Path allowed"
    return False, "Path outside allowed scopes"

