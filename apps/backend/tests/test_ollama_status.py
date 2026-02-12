from fastapi.testclient import TestClient

from app.main import app
from app.services import ollama_status


def test_ollama_status_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ollama_status.get_cached_ollama_status",
        lambda: {
            "installed": False,
            "healthy": False,
            "models_count": 0,
            "last_checked_at": "2026-01-01T00:00:00+00:00",
            "next_check_in_seconds": 10,
            "fallback_mode_active": True,
            "install_prompt_suppressed": False,
            "install_prompt_suppressed_until": None,
        },
    )
    client = TestClient(app)
    resp = client.get("/api/v1/ollama/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["healthy"] is False
    assert body["next_check_in_seconds"] == 10


def test_ollama_prompt_and_remind_later(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ollama_status.record_install_prompt",
        lambda: {"launched": True, "url": ollama_status.OLLAMA_INSTALL_URL, "detail": "Open this URL"},
    )
    monkeypatch.setattr(
        "app.services.ollama_status.remind_later",
        lambda minutes: {"status": "ok", "remind_after_minutes": minutes},
    )
    client = TestClient(app)
    install = client.post("/api/v1/ollama/install/prompt")
    assert install.status_code == 200
    assert install.json()["launched"] is True
    snooze = client.post("/api/v1/ollama/install/remind-later")
    assert snooze.status_code == 200
    assert snooze.json()["status"] == "ok"
