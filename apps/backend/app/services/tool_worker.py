"""Subprocess worker for local file tools only (no network tools)."""

from __future__ import annotations

import json
import traceback
import sys

from app.plugins.registry import PLUGIN_REGISTRY


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        tool = payload["tool"]
        args = payload.get("args", {})
        if tool not in PLUGIN_REGISTRY:
            raise ValueError(f"Unknown tool: {tool}")
        result = PLUGIN_REGISTRY[tool].run(args)
        sys.stdout.write(json.dumps({"ok": True, "result": result}))
        return 0
    except Exception as exc:
        err = {"ok": False, "error": str(exc), "trace": traceback.format_exc(limit=3)}
        sys.stdout.write(json.dumps(err))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
