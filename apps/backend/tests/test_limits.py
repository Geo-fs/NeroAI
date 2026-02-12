import time

from app.services.limits import RunLimiter, enforce_rate_limit


def test_run_limiter_tool_calls_and_files() -> None:
    limiter = RunLimiter(
        max_tool_calls_per_message=2,
        max_tool_calls_per_minute=5,
        max_files_read_per_run=1,
        max_bytes_read_per_run=10,
        max_runtime_seconds=5,
        session_id="s1",
    )
    limiter.check_tool_call()
    limiter.record_tool_call()
    limiter.check_tool_call()
    limiter.record_tool_call()
    try:
        limiter.check_tool_call()
        assert False, "Expected tool call limit error"
    except RuntimeError:
        pass

    limiter.record_file_reads(1, 5)
    try:
        limiter.record_file_reads(1, 1)
        assert False, "Expected file read count error"
    except RuntimeError:
        pass


def test_rate_limit_window() -> None:
    session_id = "rate-test"
    for _ in range(3):
        enforce_rate_limit(session_id, max_per_minute=3)
    try:
        enforce_rate_limit(session_id, max_per_minute=3)
        assert False, "Expected rate limit error"
    except RuntimeError:
        pass
    time.sleep(1)
