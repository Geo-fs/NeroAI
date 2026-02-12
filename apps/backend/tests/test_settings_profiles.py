from app.services.settings_profiles import (
    activate_profile,
    create_profile,
    delete_profile,
    export_profile,
    import_profile,
    list_profiles,
    rollback_profile,
    reset_category,
    update_profile,
)
from app.services.settings_service import get_settings


def test_profile_crud_and_apply() -> None:
    created = create_profile("Test Profile", {"privacy_mode": True})
    assert created["name"] == "Test Profile"
    updated = update_profile(created["id"], {"safe_mode_default": True}, name="Renamed")
    assert updated["name"] == "Renamed"
    assert updated["version"] >= 1

    applied = activate_profile(created["id"])
    assert applied["is_active"] == 1
    settings = get_settings()
    assert settings.safe_mode_default is True

    delete_profile(created["id"])
    assert all(p["id"] != created["id"] for p in list_profiles())


def test_import_export_validation() -> None:
    created = create_profile("Exported", {"privacy_mode": True})
    data = export_profile(created["id"])
    assert data["name"] == "Exported"
    imported = import_profile({"name": "Imported", "payload": data["payload"]})
    assert imported["name"] == "Imported"

    try:
        import_profile({"name": "Bad", "payload": "not-an-object"})  # type: ignore[arg-type]
        assert False, "Expected ValueError for invalid payload"
    except ValueError:
        pass


def test_safe_default_enforcement() -> None:
    created = create_profile("Unsafe", {"privacy_mode": False, "allow_query_text_logging": True})
    updated = update_profile(created["id"], {"privacy_mode": True, "allow_query_text_logging": True})
    data = export_profile(updated["id"])
    assert data["payload"]["privacy_mode"] is True
    assert data["payload"]["allow_query_text_logging"] is False


def test_profile_rollback() -> None:
    created = create_profile("Rollback", {"safe_mode_default": True})
    update_profile(created["id"], {"safe_mode_default": False})
    rolled = rollback_profile(created["id"])
    payload = export_profile(rolled["id"])["payload"]
    assert payload["safe_mode_default"] is True


def test_profile_reset_category() -> None:
    created = create_profile("Reset", {"verbose_logging": True})
    reset = reset_category(created["id"], ["verbose_logging"])
    payload = export_profile(reset["id"])["payload"]
    assert payload["verbose_logging"] is False
