"""Ephemeral screen capture store with TTL cleanup."""

from __future__ import annotations

import time
import uuid
from typing import Any


CAPTURE_TTL_SECONDS = 600
MAX_CAPTURES = 1
_CAPTURES: dict[str, dict[str, Any]] = {}


def cleanup_captures(now: float | None = None) -> None:
    ts = now if now is not None else time.time()
    stale = [cid for cid, item in _CAPTURES.items() if ts - item["timestamp"] > CAPTURE_TTL_SECONDS]
    for cid in stale:
        _CAPTURES.pop(cid, None)


def store_capture(
    source: str,
    image_data_url: str | None = None,
    region: dict[str, int] | None = None,
    store_thumbnail: bool = False,
) -> dict[str, Any]:
    cleanup_captures()
    capture_id = str(uuid.uuid4())
    payload = {
        "capture_id": capture_id,
        "timestamp": time.time(),
        "source": source,
        "region": region,
        "thumbnail_data_url": image_data_url if store_thumbnail else None,
        "image_data_url": image_data_url if store_thumbnail else None,
    }
    _CAPTURES[capture_id] = payload
    # Keep only last N captures.
    if len(_CAPTURES) > MAX_CAPTURES:
        for old in sorted(_CAPTURES.values(), key=lambda x: x["timestamp"])[:-MAX_CAPTURES]:
            _CAPTURES.pop(old["capture_id"], None)
    return payload


def get_capture(capture_id: str) -> dict[str, Any] | None:
    cleanup_captures()
    return _CAPTURES.get(capture_id)
