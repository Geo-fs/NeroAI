from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import GrantPermissionRequest, SettingsUpdateRequest
from app.services.permission_broker import grant_permission
from app.services.settings_service import update_settings


def test_screen_capture_requires_permission() -> None:
    client = TestClient(app)
    update_settings(SettingsUpdateRequest(safe_mode_default=False))
    response = client.post(
        "/api/v1/screen/capture",
        json={"source": "active_window", "image_data_url": "data:image/png;base64,abc"},
        headers={"X-Session-Id": "s1"},
    )
    assert response.status_code == 403


def test_screen_capture_with_grant_succeeds() -> None:
    client = TestClient(app)
    update_settings(SettingsUpdateRequest(safe_mode_default=False))
    grant_permission(GrantPermissionRequest(permission="screen.capture", scope="session"), session_id="s1")
    response = client.post(
        "/api/v1/screen/capture",
        json={"source": "active_window", "image_data_url": "data:image/png;base64,abc"},
        headers={"X-Session-Id": "s1"},
    )
    assert response.status_code == 200
    assert response.json().get("capture_id")


def test_clipboard_requires_permission() -> None:
    client = TestClient(app)
    update_settings(SettingsUpdateRequest(safe_mode_default=False))
    response = client.post("/api/v1/clipboard/read", headers={"X-Session-Id": "s1"})
    assert response.status_code == 403
