from app.services import screen_capture


def test_capture_ttl_cleanup() -> None:
    screen_capture._CAPTURES.clear()  # type: ignore[attr-defined]
    item = screen_capture.store_capture(source="active_window", image_data_url="data:image/png;base64,abc")
    cid = item["capture_id"]
    assert screen_capture.get_capture(cid) is not None
    future = item["timestamp"] + screen_capture.CAPTURE_TTL_SECONDS + 1
    screen_capture.cleanup_captures(now=future)
    assert screen_capture.get_capture(cid) is None


def test_capture_keeps_only_last_one() -> None:
    screen_capture._CAPTURES.clear()  # type: ignore[attr-defined]
    first = screen_capture.store_capture(source="active_window")
    second = screen_capture.store_capture(source="active_window")
    assert screen_capture.get_capture(second["capture_id"]) is not None
    assert screen_capture.get_capture(first["capture_id"]) is None
