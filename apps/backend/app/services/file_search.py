"""Filesystem search helper."""

from __future__ import annotations

from pathlib import Path


def search_files(path: str, pattern: str = "*", max_results: int = 100) -> list[str]:
    base = Path(path).resolve()
    if not base.exists():
        return []
    results: list[str] = []
    for item in base.rglob(pattern):
        if item.is_file():
            results.append(str(item))
            if len(results) >= max_results:
                break
    return results
