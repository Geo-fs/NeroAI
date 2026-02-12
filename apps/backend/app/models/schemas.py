"""Pydantic request/response contracts for API v1."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


PermissionType = Literal[
    "filesystem.read",
    "filesystem.write",
    "web.search",
    "screen.capture",
    "clipboard.read",
    "clipboard.write",
    "process.run",
]
GrantScope = Literal["once", "session", "always"]
SearchProviderName = Literal["duckduckgo_html", "local_browser", "manual"]


class HealthResponse(BaseModel):
    status: str = "ok"


class ModelSourceCreate(BaseModel):
    name: str
    base_url: str
    auth_token: str | None = None


class ModelSourceResponse(BaseModel):
    id: str
    name: str
    base_url: str
    is_local: bool
    has_auth_token: bool = False
    created_at: str | None = None


class ModelOptionResponse(BaseModel):
    source_id: str
    source_name: str
    model: str
    base_url: str


class SourceTestResponse(BaseModel):
    ok: bool
    detail: str


class ChatRequest(BaseModel):
    source_id: str
    model: str
    message: str
    mode: Literal["chat", "workflow"] = "chat"
    context: dict[str, Any] = Field(default_factory=dict)


class PermissionCheckRequest(BaseModel):
    permission: PermissionType
    path: str | None = None


class PermissionCheckResponse(BaseModel):
    granted: bool
    reason: str


class GrantPermissionRequest(BaseModel):
    permission: PermissionType
    scope: GrantScope = "once"
    allowed_paths: list[str] = Field(default_factory=list)


class PermissionGrantResponse(BaseModel):
    permission: PermissionType
    scope: GrantScope
    session_id: str | None = None
    allowed_paths: list[str] = Field(default_factory=list)


class WorkflowSaveRequest(BaseModel):
    id: str | None = None
    name: str
    description: str = ""
    definition: dict[str, Any]


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    definition: dict[str, Any]


class WorkflowRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    result: dict[str, Any]
    run_id: str | None = None


class RunResponse(BaseModel):
    id: str
    session_id: str | None = None
    mode: str
    input_hash: str
    input_text: str | None = None
    model_source_id: str | None = None
    model_name: str | None = None
    created_at: str | None = None
    duration_ms: int | None = None


class RunDetailResponse(RunResponse):
    events: list[dict[str, Any]] = Field(default_factory=list)


class RunReplayResponse(BaseModel):
    run_id: str
    steps: list[dict[str, Any]] = Field(default_factory=list)


class ArtifactCreateRequest(BaseModel):
    name: str
    content: str
    type: str
    run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    id: str
    run_id: str | None = None
    type: str
    name: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class MemoryCreateRequest(BaseModel):
    kind: Literal["preference", "project_fact"]
    content: str


class MemoryUpdateRequest(BaseModel):
    content: str


class MemoryResponse(BaseModel):
    id: str
    kind: str
    content: str
    created_at: str | None = None
    updated_at: str | None = None


class PluginResponse(BaseModel):
    id: str | None = None
    name: str
    type: Literal["builtin", "local"]
    enabled: bool
    version: str | None = None
    path: str | None = None


class PluginToggleRequest(BaseModel):
    enabled: bool


class VectorIndexItem(BaseModel):
    path: str
    content: str
    content_hash: str


class VectorIndexRequest(BaseModel):
    workspace_id: str
    items: list[VectorIndexItem]


class VectorSearchRequest(BaseModel):
    workspace_id: str
    query: str
    limit: int = 5


class VectorSearchResponse(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)


class DiagnosticsExportResponse(BaseModel):
    path: str


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source_name: str
    rank: int


class ManualSearchSubmitRequest(BaseModel):
    query: str
    json_results: list[SearchResult] | None = None
    pasted_lines: str | None = None


class SearchRequest(BaseModel):
    query: str
    num_results: int = 5
    safe: bool = True
    manual_payload: ManualSearchSubmitRequest | None = None


class SearchResponse(BaseModel):
    status: Literal["ok", "manual_required", "error"]
    provider: SearchProviderName
    results: list[SearchResult] = Field(default_factory=list)
    detail: str = ""
    manual_instructions: str | None = None


class SettingsResponse(BaseModel):
    safe_mode_default: bool = True
    privacy_mode: bool = True
    redaction_enabled: bool = True
    allow_query_text_logging: bool = False
    verbose_logging: bool = False
    policy_rules: str = ""
    search_provider: SearchProviderName = "duckduckgo_html"
    local_browser_enabled: bool = False
    local_browser_headed: bool = True
    local_browser_engine: Literal["chrome", "chromium"] = "chrome"
    max_tool_calls_per_message: int = 3
    max_tool_calls_per_minute: int = 15
    max_files_read_per_run: int = 20
    max_bytes_read_per_run: int = 5_000_000
    max_runtime_seconds: int = 120
    write_preview_default: bool = True
    quarantine_mode: bool = True
    use_saved_memory: bool = False
    reviewer_enabled: bool = False
    reviewer_strictness: Literal["low", "standard", "strict"] = "standard"
    dry_run_mode: Literal["always", "ask", "never"] = "ask"
    thinkbox_enabled: bool = True
    thinkbox_hotkey: str = "Control+Alt+Space"
    thinkbox_position: Literal["bottom-right", "near-cursor", "custom"] = "bottom-right"
    thinkbox_size_percent: int = 20
    thinkbox_auto_hide_seconds: int = 30
    thinkbox_pin_default: bool = False
    thinkbox_no_focus_steal: bool = False
    thinkbox_capture_default: Literal["active_window", "region"] = "active_window"
    thinkbox_awareness_default: bool = False
    thinkbox_awareness_minutes: int = 10
    thinkbox_awareness_interval_seconds: int = 0
    thinkbox_store_screenshots: bool = False
    thinkbox_store_thumbnail: bool = False
    ollama_required_for_local_chat: bool = True
    ollama_check_interval_seconds: int = 10
    ollama_install_prompt_enabled: bool = True
    ollama_remind_later_minutes: int = 60
    ollama_fallback_mode: Literal["search_answer", "remote_only", "block"] = "search_answer"


class SettingsUpdateRequest(BaseModel):
    safe_mode_default: bool | None = None
    privacy_mode: bool | None = None
    redaction_enabled: bool | None = None
    allow_query_text_logging: bool | None = None
    verbose_logging: bool | None = None
    policy_rules: str | None = None
    search_provider: SearchProviderName | None = None
    local_browser_enabled: bool | None = None
    local_browser_headed: bool | None = None
    local_browser_engine: Literal["chrome", "chromium"] | None = None
    max_tool_calls_per_message: int | None = None
    max_tool_calls_per_minute: int | None = None
    max_files_read_per_run: int | None = None
    max_bytes_read_per_run: int | None = None
    max_runtime_seconds: int | None = None
    write_preview_default: bool | None = None
    quarantine_mode: bool | None = None
    use_saved_memory: bool | None = None
    reviewer_enabled: bool | None = None
    reviewer_strictness: Literal["low", "standard", "strict"] | None = None
    dry_run_mode: Literal["always", "ask", "never"] | None = None
    thinkbox_enabled: bool | None = None
    thinkbox_hotkey: str | None = None
    thinkbox_position: Literal["bottom-right", "near-cursor", "custom"] | None = None
    thinkbox_size_percent: int | None = None
    thinkbox_auto_hide_seconds: int | None = None
    thinkbox_pin_default: bool | None = None
    thinkbox_no_focus_steal: bool | None = None
    thinkbox_capture_default: Literal["active_window", "region"] | None = None
    thinkbox_awareness_default: bool | None = None
    thinkbox_awareness_minutes: int | None = None
    thinkbox_awareness_interval_seconds: int | None = None
    thinkbox_store_screenshots: bool | None = None
    thinkbox_store_thumbnail: bool | None = None
    ollama_required_for_local_chat: bool | None = None
    ollama_check_interval_seconds: int | None = None
    ollama_install_prompt_enabled: bool | None = None
    ollama_remind_later_minutes: int | None = None
    ollama_fallback_mode: Literal["search_answer", "remote_only", "block"] | None = None


class SettingsProfileCreateRequest(BaseModel):
    name: str
    payload: dict[str, Any] | None = None


class SettingsProfileUpdateRequest(BaseModel):
    name: str | None = None
    payload: dict[str, Any]


class SettingsProfileResponse(BaseModel):
    id: str
    name: str
    version: int | None = None
    is_active: bool
    payload: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SettingsProfileExportResponse(BaseModel):
    id: str
    name: str
    version: int
    payload: dict[str, Any]


class SettingsProfileImportRequest(BaseModel):
    name: str | None = None
    payload: dict[str, Any]


class SettingsProfileDuplicateRequest(BaseModel):
    name: str | None = None


class SettingsRegistryEntry(BaseModel):
    key: str
    type: str
    default: Any
    category: str
    scope: str
    danger: str
    requires_restart: bool
    description: str
    enum_values: list[str] | None = None


class SecretSetRequest(BaseModel):
    key_name: str
    value: str


class SecretStatusResponse(BaseModel):
    key_name: str
    configured: bool


class PolicyValidateRequest(BaseModel):
    text: str


class PolicyValidateResponse(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)


class PolicyTestRequest(BaseModel):
    action: str
    confirmed: bool = False


class PolicyTestResponse(BaseModel):
    allowed: bool
    reason: str


class WorkspaceCreateRequest(BaseModel):
    name: str
    description: str | None = ""
    scopes: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
    default_profile_id: str | None = None
    default_model_source_id: str | None = None
    default_model: str | None = None
    logging_strictness: Literal["standard", "strict"] = "standard"


class WorkspaceUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    scopes: list[str] | None = None
    allowed_tools: list[str] | None = None
    settings: dict[str, Any] | None = None
    default_profile_id: str | None = None
    default_model_source_id: str | None = None
    default_model: str | None = None
    logging_strictness: Literal["standard", "strict"] | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: str
    scopes: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
    default_profile_id: str | None = None
    default_model_source_id: str | None = None
    default_model: str | None = None
    logging_strictness: Literal["standard", "strict"] = "standard"
    is_active: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class ToolRunPolicy(BaseModel):
    timeout_seconds: int = 30
    output_limit_bytes: int = 262_144


class SecurityPlanResponse(BaseModel):
    rule_name: str
    tool_runner_program: str
    create_rule_command: str
    status_check_command: str


class SecurityStatusResponse(BaseModel):
    rule_name: str
    tool_runner_program: str
    exists: bool
    enabled: bool
    outbound_block: bool
    program_matches: bool
    confirmed_blocking: bool
    detail: str = ""


class SecurityLockdownResponse(BaseModel):
    launched: bool
    requires_uac: bool = True
    detail: str


class OllamaStatusResponse(BaseModel):
    installed: bool
    healthy: bool
    models_count: int
    last_checked_at: str
    next_check_in_seconds: int
    fallback_mode_active: bool
    install_prompt_suppressed: bool = False
    install_prompt_suppressed_until: str | None = None


class OllamaInstallPromptResponse(BaseModel):
    launched: bool
    url: str
    detail: str


class OllamaRemindLaterResponse(BaseModel):
    status: Literal["ok"] = "ok"
    remind_after_minutes: int


class ThinkBoxMessageRequest(BaseModel):
    text: str
    mode: Literal["screen_help", "explain", "steps", "extract", "research"] = "screen_help"
    toggles: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    model_source_id: str | None = None
    model: str | None = None


class ThinkBoxMessageResponse(BaseModel):
    run_id: str


class ScreenCaptureRegion(BaseModel):
    x: int
    y: int
    w: int
    h: int


class ScreenCaptureRequest(BaseModel):
    source: Literal["active_window", "region"] = "active_window"
    region: ScreenCaptureRegion | None = None
    image_data_url: str | None = None


class ScreenCaptureResponse(BaseModel):
    capture_id: str
    timestamp: float
    thumbnail_data_url: str | None = None


class ClipboardWriteRequest(BaseModel):
    text: str


class ClipboardReadResponse(BaseModel):
    text: str


class FileSearchRequest(BaseModel):
    path: str
    pattern: str = "*"
    max_results: int = 100


class FileSearchResponse(BaseModel):
    results: list[str] = Field(default_factory=list)
