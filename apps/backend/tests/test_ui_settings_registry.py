from app.services.settings_registry import registry_entries


def test_ui_category_contains_many_options() -> None:
    entries = registry_entries()
    ui_entries = [item for item in entries if item["category"] == "UI"]
    assert len(ui_entries) >= 50


def test_thinkbox_settings_exist_in_ui_category() -> None:
    entries = registry_entries()
    keys = {item["key"] for item in entries if item["category"] == "UI"}
    assert "thinkbox_hotkey" in keys
    assert "thinkbox_default_mode" in keys
    assert "ui_theme_mode" in keys
