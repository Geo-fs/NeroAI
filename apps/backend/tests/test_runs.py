from app.services.run_logger import get_run, list_runs, log_run_event, start_run, finish_run


def test_run_logging() -> None:
    run = start_run(session_id="s1", mode="chat", input_text="hello", model_source_id=None, model_name=None)
    log_run_event(run["id"], "test.event", {"ok": True})
    finish_run(run["id"], run["start"])
    fetched = get_run(run["id"])
    assert fetched is not None
    assert any(e["event_type"] == "test.event" for e in fetched["events"])
    assert any(r["id"] == run["id"] for r in list_runs(limit=10))
