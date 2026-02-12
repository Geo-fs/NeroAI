"""Settings registry defining keys, defaults, categories, and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, field_validator


Scope = Literal["global", "profile", "workspace"]
DangerLevel = Literal["normal", "advanced", "admin"]


@dataclass(frozen=True)
class SettingDef:
    key: str
    type: Literal["bool", "int", "float", "string", "enum"]
    default: Any
    category: str
    scope: Scope
    danger: DangerLevel = "normal"
    requires_restart: bool = False
    description: str = ""
    enum_values: list[str] | None = None


class SettingsPayload(BaseModel):
    safe_mode_default: bool = True
    privacy_mode: bool = True
    redaction_enabled: bool = True
    allow_query_text_logging: bool = False
    verbose_logging: bool = False
    policy_rules: str = ""
    search_provider: str = "duckduckgo_html"
    local_browser_enabled: bool = False
    local_browser_headed: bool = True
    local_browser_engine: str = "chrome"
    max_tool_calls_per_message: int = 3
    max_tool_calls_per_minute: int = 15
    max_files_read_per_run: int = 20
    max_bytes_read_per_run: int = 5_000_000
    max_runtime_seconds: int = 120
    write_preview_default: bool = True
    quarantine_mode: bool = True
    use_saved_memory: bool = False
    reviewer_enabled: bool = False
    reviewer_strictness: str = "standard"
    dry_run_mode: str = "ask"
    thinkbox_enabled: bool = True
    thinkbox_hotkey: str = "Control+Alt+Space"
    thinkbox_position: str = "bottom-right"
    thinkbox_size_percent: int = 20
    thinkbox_auto_hide_seconds: int = 30
    thinkbox_pin_default: bool = False
    thinkbox_no_focus_steal: bool = False
    thinkbox_capture_default: str = "active_window"
    thinkbox_awareness_default: bool = False
    thinkbox_awareness_minutes: int = 10
    thinkbox_awareness_interval_seconds: int = 0
    thinkbox_store_screenshots: bool = False
    thinkbox_store_thumbnail: bool = False
    ollama_required_for_local_chat: bool = True
    ollama_check_interval_seconds: int = 10
    ollama_install_prompt_enabled: bool = True
    ollama_remind_later_minutes: int = 60
    ollama_fallback_mode: str = "search_answer"
    ui_density: str = "comfortable"
    ui_font_scale_percent: int = 100
    ui_sidebar_collapsed: bool = False
    ui_sidebar_width: int = 240
    ui_show_topbar: bool = True
    ui_topbar_compact: bool = False
    ui_show_command_palette_hint: bool = True
    ui_animations_enabled: bool = True
    ui_animation_speed: str = "normal"
    ui_reduce_motion: bool = False
    ui_high_contrast: bool = False
    ui_theme_mode: str = "system"
    ui_theme_accent: str = "blue"
    ui_card_roundness: int = 12
    ui_card_shadow_level: str = "medium"
    ui_border_style: str = "soft"
    ui_focus_ring_enabled: bool = True
    ui_focus_ring_thickness: int = 2
    ui_spacing_scale_percent: int = 100
    ui_chat_line_height_percent: int = 145
    ui_chat_show_timestamps: bool = False
    ui_chat_show_role_badges: bool = True
    ui_chat_streaming_cursor: bool = True
    ui_chat_autoscroll: bool = True
    ui_chat_compact_mode: bool = False
    ui_chat_input_rows: int = 4
    ui_chat_send_on_enter: bool = False
    ui_chat_show_run_report_link: bool = True
    ui_audit_rows_per_page: int = 50
    ui_workflow_editor_font_size: int = 13
    ui_settings_show_descriptions: bool = True
    ui_settings_show_advanced_badges: bool = True
    ui_settings_remember_last_category: bool = True
    ui_palette_max_results: int = 12
    ui_palette_blur_background: bool = True
    thinkbox_opacity_percent: int = 98
    thinkbox_corner_roundness: int = 10
    thinkbox_border_width: int = 1
    thinkbox_border_color: str = "#d7e2f0"
    thinkbox_background_blur: bool = False
    thinkbox_show_connection_dot: bool = True
    thinkbox_show_safe_mode_badge: bool = True
    thinkbox_show_mode_chips: bool = True
    thinkbox_default_mode: str = "screen_help"
    thinkbox_response_bullet_min: int = 3
    thinkbox_response_bullet_max: int = 8
    thinkbox_expand_by_default: bool = False
    thinkbox_enable_ctrl_l_focus: bool = True
    thinkbox_enable_enter_to_send: bool = True
    thinkbox_show_capture_thumbnail: bool = True
    thinkbox_thumbnail_height: int = 120
    thinkbox_region_selector_grid: bool = True
    thinkbox_capture_quality: str = "medium"
    thinkbox_capture_on_open: bool = False
    thinkbox_capture_on_mode_change: bool = False
    thinkbox_awareness_show_countdown: bool = True
    thinkbox_awareness_require_pin: bool = True
    thinkbox_awareness_pause_when_unfocused: bool = True
    thinkbox_quick_action_copy: bool = True
    thinkbox_quick_action_steps: bool = True
    thinkbox_quick_action_research: bool = True
    thinkbox_quick_action_clipboard: bool = True
    thinkbox_allow_no_focus_steal_toggle: bool = True
    thinkbox_hide_when_main_focus: bool = False
    thinkbox_remember_last_text: bool = False
    thinkbox_clear_text_on_send: bool = False
    thinkbox_status_toast_seconds: int = 3

    @field_validator("search_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        allowed = {"duckduckgo_html", "local_browser", "manual"}
        if value not in allowed:
            raise ValueError("Invalid search provider")
        return value

    @field_validator("ollama_fallback_mode")
    @classmethod
    def validate_ollama_fallback_mode(cls, value: str) -> str:
        allowed = {"search_answer", "remote_only", "block"}
        if value not in allowed:
            raise ValueError("Invalid ollama fallback mode")
        return value


REGISTRY: list[SettingDef] = [
    SettingDef(
        key="safe_mode_default",
        type="bool",
        default=True,
        category="Security",
        scope="profile",
        danger="normal",
        description="Default Safe Mode for new sessions.",
    ),
    SettingDef(
        key="privacy_mode",
        type="bool",
        default=True,
        category="Logging",
        scope="profile",
        danger="normal",
        description="Store only hashed queries and minimal logs.",
    ),
    SettingDef(
        key="redaction_enabled",
        type="bool",
        default=True,
        category="Logging",
        scope="profile",
        danger="normal",
        description="Redact sensitive values from logs and telemetry.",
    ),
    SettingDef(
        key="policy_rules",
        type="string",
        default="",
        category="Security",
        scope="profile",
        danger="advanced",
        description="Policy-as-code rules for tool and permission decisions.",
    ),
    SettingDef(
        key="allow_query_text_logging",
        type="bool",
        default=False,
        category="Logging",
        scope="profile",
        danger="advanced",
        description="Allow raw query logging (only when privacy mode is off).",
    ),
    SettingDef(
        key="verbose_logging",
        type="bool",
        default=False,
        category="Logging",
        scope="profile",
        danger="advanced",
        description="Store truncated samples of tool inputs/outputs.",
    ),
    SettingDef(
        key="search_provider",
        type="enum",
        default="duckduckgo_html",
        category="Search",
        scope="profile",
        danger="normal",
        enum_values=["duckduckgo_html", "local_browser", "manual"],
    ),
    SettingDef(
        key="local_browser_enabled",
        type="bool",
        default=False,
        category="Search",
        scope="profile",
    ),
    SettingDef(
        key="local_browser_headed",
        type="bool",
        default=True,
        category="Search",
        scope="profile",
    ),
    SettingDef(
        key="local_browser_engine",
        type="enum",
        default="chrome",
        category="Search",
        scope="profile",
        enum_values=["chrome", "chromium"],
    ),
    SettingDef(
        key="max_tool_calls_per_message",
        type="int",
        default=3,
        category="Tools",
        scope="profile",
        danger="advanced",
        description="Maximum tool calls allowed per user message.",
    ),
    SettingDef(
        key="max_tool_calls_per_minute",
        type="int",
        default=15,
        category="Tools",
        scope="profile",
        danger="advanced",
        description="Rate limit for tool calls per minute.",
    ),
    SettingDef(
        key="max_files_read_per_run",
        type="int",
        default=20,
        category="Tools",
        scope="profile",
        danger="advanced",
        description="Maximum number of files a run can read.",
    ),
    SettingDef(
        key="max_bytes_read_per_run",
        type="int",
        default=5_000_000,
        category="Tools",
        scope="profile",
        danger="advanced",
        description="Maximum total bytes read per run.",
    ),
    SettingDef(
        key="max_runtime_seconds",
        type="int",
        default=120,
        category="Agent Runtime",
        scope="profile",
        danger="advanced",
        description="Maximum runtime seconds per run.",
    ),
    SettingDef(
        key="write_preview_default",
        type="bool",
        default=True,
        category="Tools",
        scope="profile",
        danger="normal",
        description="Require preview/confirmation before file writes.",
    ),
    SettingDef(
        key="quarantine_mode",
        type="bool",
        default=True,
        category="Tools",
        scope="profile",
        danger="advanced",
        description="Copy out-of-scope files to a temporary quarantine before reading.",
    ),
    SettingDef(
        key="use_saved_memory",
        type="bool",
        default=False,
        category="Agent Runtime",
        scope="profile",
        danger="normal",
        description="Allow use of saved memory items in responses.",
    ),
    SettingDef(
        key="reviewer_enabled",
        type="bool",
        default=False,
        category="Agent Runtime",
        scope="profile",
        danger="advanced",
        description="Enable reviewer pass on responses.",
    ),
    SettingDef(
        key="reviewer_strictness",
        type="enum",
        default="standard",
        category="Agent Runtime",
        scope="profile",
        danger="advanced",
        enum_values=["low", "standard", "strict"],
        description="Reviewer strictness level.",
    ),
    SettingDef(
        key="dry_run_mode",
        type="enum",
        default="ask",
        category="Workflows",
        scope="profile",
        danger="advanced",
        enum_values=["always", "ask", "never"],
        description="Dry run behavior before tool execution.",
    ),
    SettingDef(
        key="thinkbox_enabled",
        type="bool",
        default=True,
        category="UI",
        scope="profile",
        description="Enable Think Box overlay window.",
    ),
    SettingDef(
        key="thinkbox_hotkey",
        type="string",
        default="Control+Alt+Space",
        category="UI",
        scope="profile",
        description="Global hotkey to toggle Think Box.",
    ),
    SettingDef(
        key="thinkbox_position",
        type="enum",
        default="bottom-right",
        category="UI",
        scope="profile",
        enum_values=["bottom-right", "near-cursor", "custom"],
    ),
    SettingDef(
        key="thinkbox_size_percent",
        type="int",
        default=20,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_auto_hide_seconds",
        type="int",
        default=30,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_pin_default",
        type="bool",
        default=False,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_no_focus_steal",
        type="bool",
        default=False,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_capture_default",
        type="enum",
        default="active_window",
        category="UI",
        scope="profile",
        enum_values=["active_window", "region"],
    ),
    SettingDef(
        key="thinkbox_awareness_default",
        type="bool",
        default=False,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_awareness_minutes",
        type="int",
        default=10,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_awareness_interval_seconds",
        type="int",
        default=0,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_store_screenshots",
        type="bool",
        default=False,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="thinkbox_store_thumbnail",
        type="bool",
        default=False,
        category="UI",
        scope="profile",
    ),
    SettingDef(
        key="ollama_required_for_local_chat",
        type="bool",
        default=True,
        category="Models",
        scope="profile",
        description="Require local Ollama for local model chat paths.",
    ),
    SettingDef(
        key="ollama_check_interval_seconds",
        type="int",
        default=10,
        category="Models",
        scope="profile",
        description="Background health check interval for local Ollama daemon.",
    ),
    SettingDef(
        key="ollama_install_prompt_enabled",
        type="bool",
        default=True,
        category="Models",
        scope="profile",
        description="Show install prompt when local Ollama is not available.",
    ),
    SettingDef(
        key="ollama_remind_later_minutes",
        type="int",
        default=60,
        category="Models",
        scope="profile",
        description="Snooze duration after choosing remind later on install prompt.",
    ),
    SettingDef(
        key="ollama_fallback_mode",
        type="enum",
        default="search_answer",
        category="Models",
        scope="profile",
        enum_values=["search_answer", "remote_only", "block"],
        description="Fallback behavior when local Ollama is unavailable.",
    ),
    SettingDef(
        key="ui_density",
        type="enum",
        default="comfortable",
        category="UI",
        scope="profile",
        enum_values=["compact", "comfortable", "cozy"],
        description="Overall control density for main app surfaces.",
    ),
    SettingDef(key="ui_font_scale_percent", type="int", default=100, category="UI", scope="profile"),
    SettingDef(key="ui_sidebar_collapsed", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="ui_sidebar_width", type="int", default=240, category="UI", scope="profile"),
    SettingDef(key="ui_show_topbar", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_topbar_compact", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="ui_show_command_palette_hint", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_animations_enabled", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(
        key="ui_animation_speed",
        type="enum",
        default="normal",
        category="UI",
        scope="profile",
        enum_values=["slow", "normal", "fast"],
    ),
    SettingDef(key="ui_reduce_motion", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="ui_high_contrast", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(
        key="ui_theme_mode",
        type="enum",
        default="system",
        category="UI",
        scope="profile",
        enum_values=["system", "light", "dark"],
    ),
    SettingDef(
        key="ui_theme_accent",
        type="enum",
        default="blue",
        category="UI",
        scope="profile",
        enum_values=["blue", "teal", "green", "orange", "red"],
    ),
    SettingDef(key="ui_card_roundness", type="int", default=12, category="UI", scope="profile"),
    SettingDef(
        key="ui_card_shadow_level",
        type="enum",
        default="medium",
        category="UI",
        scope="profile",
        enum_values=["none", "low", "medium", "high"],
    ),
    SettingDef(
        key="ui_border_style",
        type="enum",
        default="soft",
        category="UI",
        scope="profile",
        enum_values=["soft", "sharp"],
    ),
    SettingDef(key="ui_focus_ring_enabled", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_focus_ring_thickness", type="int", default=2, category="UI", scope="profile"),
    SettingDef(key="ui_spacing_scale_percent", type="int", default=100, category="UI", scope="profile"),
    SettingDef(key="ui_chat_line_height_percent", type="int", default=145, category="UI", scope="profile"),
    SettingDef(key="ui_chat_show_timestamps", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="ui_chat_show_role_badges", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_chat_streaming_cursor", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_chat_autoscroll", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_chat_compact_mode", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="ui_chat_input_rows", type="int", default=4, category="UI", scope="profile"),
    SettingDef(key="ui_chat_send_on_enter", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="ui_chat_show_run_report_link", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_audit_rows_per_page", type="int", default=50, category="UI", scope="profile"),
    SettingDef(key="ui_workflow_editor_font_size", type="int", default=13, category="UI", scope="profile"),
    SettingDef(key="ui_settings_show_descriptions", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_settings_show_advanced_badges", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_settings_remember_last_category", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="ui_palette_max_results", type="int", default=12, category="UI", scope="profile"),
    SettingDef(key="ui_palette_blur_background", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_opacity_percent", type="int", default=98, category="UI", scope="profile"),
    SettingDef(key="thinkbox_corner_roundness", type="int", default=10, category="UI", scope="profile"),
    SettingDef(key="thinkbox_border_width", type="int", default=1, category="UI", scope="profile"),
    SettingDef(key="thinkbox_border_color", type="string", default="#d7e2f0", category="UI", scope="profile"),
    SettingDef(key="thinkbox_background_blur", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_show_connection_dot", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_show_safe_mode_badge", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_show_mode_chips", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(
        key="thinkbox_default_mode",
        type="enum",
        default="screen_help",
        category="UI",
        scope="profile",
        enum_values=["screen_help", "explain", "steps", "extract", "research"],
    ),
    SettingDef(key="thinkbox_response_bullet_min", type="int", default=3, category="UI", scope="profile"),
    SettingDef(key="thinkbox_response_bullet_max", type="int", default=8, category="UI", scope="profile"),
    SettingDef(key="thinkbox_expand_by_default", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_enable_ctrl_l_focus", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_enable_enter_to_send", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_show_capture_thumbnail", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_thumbnail_height", type="int", default=120, category="UI", scope="profile"),
    SettingDef(key="thinkbox_region_selector_grid", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(
        key="thinkbox_capture_quality",
        type="enum",
        default="medium",
        category="UI",
        scope="profile",
        enum_values=["low", "medium", "high"],
    ),
    SettingDef(key="thinkbox_capture_on_open", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_capture_on_mode_change", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_awareness_show_countdown", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_awareness_require_pin", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_awareness_pause_when_unfocused", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_quick_action_copy", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_quick_action_steps", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_quick_action_research", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_quick_action_clipboard", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_allow_no_focus_steal_toggle", type="bool", default=True, category="UI", scope="profile"),
    SettingDef(key="thinkbox_hide_when_main_focus", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_remember_last_text", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_clear_text_on_send", type="bool", default=False, category="UI", scope="profile"),
    SettingDef(key="thinkbox_status_toast_seconds", type="int", default=3, category="UI", scope="profile"),
]


def registry_defaults() -> dict[str, Any]:
    return {item.key: item.default for item in REGISTRY}


def registry_entries() -> list[dict[str, Any]]:
    return [
        {
            "key": item.key,
            "type": item.type,
            "default": item.default,
            "category": item.category,
            "scope": item.scope,
            "danger": item.danger,
            "requires_restart": item.requires_restart,
            "description": item.description,
            "enum_values": item.enum_values,
        }
        for item in REGISTRY
    ]


def registry_by_key() -> dict[str, SettingDef]:
    return {item.key: item for item in REGISTRY}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and coerce settings via pydantic model."""
    model = SettingsPayload(**payload)
    return model.model_dump()


def enforce_safe_defaults(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload["safe_mode_default"] = True if payload.get("safe_mode_default") is not False else False
    payload["privacy_mode"] = True if payload.get("privacy_mode") is not False else False
    payload["redaction_enabled"] = True if payload.get("redaction_enabled") is not False else False
    if payload.get("privacy_mode"):
        payload["allow_query_text_logging"] = False
    return payload
