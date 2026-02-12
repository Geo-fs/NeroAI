export type PermissionType =
  | "filesystem.read"
  | "filesystem.write"
  | "web.search"
  | "screen.capture"
  | "clipboard.read"
  | "clipboard.write"
  | "process.run";

export type SearchProviderName = "duckduckgo_html" | "local_browser" | "manual";

export interface ModelOption {
  source_id: string;
  source_name: string;
  model: string;
  base_url: string;
}

export interface MessageItem {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface RemoteSourceInput {
  name: string;
  base_url: string;
  auth_token?: string;
}

export interface WorkflowDef {
  id: string;
  name: string;
  description: string;
  definition: Record<string, unknown>;
}

export interface SettingsDef {
  [key: string]: unknown;
  safe_mode_default: boolean;
  privacy_mode: boolean;
  redaction_enabled: boolean;
  allow_query_text_logging: boolean;
  verbose_logging: boolean;
  policy_rules: string;
  search_provider: SearchProviderName;
  local_browser_enabled: boolean;
  local_browser_headed: boolean;
  local_browser_engine: "chrome" | "chromium";
  max_tool_calls_per_message: number;
  max_tool_calls_per_minute: number;
  max_files_read_per_run: number;
  max_bytes_read_per_run: number;
  max_runtime_seconds: number;
  write_preview_default: boolean;
  quarantine_mode: boolean;
  use_saved_memory: boolean;
  reviewer_enabled: boolean;
  reviewer_strictness: "low" | "standard" | "strict";
  dry_run_mode: "always" | "ask" | "never";
  thinkbox_enabled: boolean;
  thinkbox_hotkey: string;
  thinkbox_position: "bottom-right" | "near-cursor" | "custom";
  thinkbox_size_percent: number;
  thinkbox_auto_hide_seconds: number;
  thinkbox_pin_default: boolean;
  thinkbox_no_focus_steal: boolean;
  thinkbox_capture_default: "active_window" | "region";
  thinkbox_awareness_default: boolean;
  thinkbox_awareness_minutes: number;
  thinkbox_awareness_interval_seconds: number;
  thinkbox_store_screenshots: boolean;
  thinkbox_store_thumbnail: boolean;
  ollama_required_for_local_chat?: boolean;
  ollama_check_interval_seconds?: number;
  ollama_install_prompt_enabled?: boolean;
  ollama_remind_later_minutes?: number;
  ollama_fallback_mode?: "search_answer" | "remote_only" | "block";
  ui_density?: "compact" | "comfortable" | "cozy";
  ui_font_scale_percent?: number;
  ui_sidebar_collapsed?: boolean;
  ui_sidebar_width?: number;
  ui_show_topbar?: boolean;
  ui_topbar_compact?: boolean;
  ui_show_command_palette_hint?: boolean;
  ui_animations_enabled?: boolean;
  ui_animation_speed?: "slow" | "normal" | "fast";
  ui_reduce_motion?: boolean;
  ui_high_contrast?: boolean;
  ui_theme_mode?: "system" | "light" | "dark";
  ui_theme_accent?: "blue" | "teal" | "green" | "orange" | "red";
  ui_card_roundness?: number;
  ui_card_shadow_level?: "none" | "low" | "medium" | "high";
  ui_border_style?: "soft" | "sharp";
  ui_focus_ring_enabled?: boolean;
  ui_focus_ring_thickness?: number;
  ui_spacing_scale_percent?: number;
  ui_chat_line_height_percent?: number;
  ui_chat_show_timestamps?: boolean;
  ui_chat_show_role_badges?: boolean;
  ui_chat_streaming_cursor?: boolean;
  ui_chat_autoscroll?: boolean;
  ui_chat_compact_mode?: boolean;
  ui_chat_input_rows?: number;
  ui_chat_send_on_enter?: boolean;
  ui_chat_show_run_report_link?: boolean;
  ui_audit_rows_per_page?: number;
  ui_workflow_editor_font_size?: number;
  ui_settings_show_descriptions?: boolean;
  ui_settings_show_advanced_badges?: boolean;
  ui_settings_remember_last_category?: boolean;
  ui_palette_max_results?: number;
  ui_palette_blur_background?: boolean;
  thinkbox_opacity_percent?: number;
  thinkbox_corner_roundness?: number;
  thinkbox_border_width?: number;
  thinkbox_border_color?: string;
  thinkbox_background_blur?: boolean;
  thinkbox_show_connection_dot?: boolean;
  thinkbox_show_safe_mode_badge?: boolean;
  thinkbox_show_mode_chips?: boolean;
  thinkbox_default_mode?: "screen_help" | "explain" | "steps" | "extract" | "research";
  thinkbox_response_bullet_min?: number;
  thinkbox_response_bullet_max?: number;
  thinkbox_expand_by_default?: boolean;
  thinkbox_enable_ctrl_l_focus?: boolean;
  thinkbox_enable_enter_to_send?: boolean;
  thinkbox_show_capture_thumbnail?: boolean;
  thinkbox_thumbnail_height?: number;
  thinkbox_region_selector_grid?: boolean;
  thinkbox_capture_quality?: "low" | "medium" | "high";
  thinkbox_capture_on_open?: boolean;
  thinkbox_capture_on_mode_change?: boolean;
  thinkbox_awareness_show_countdown?: boolean;
  thinkbox_awareness_require_pin?: boolean;
  thinkbox_awareness_pause_when_unfocused?: boolean;
  thinkbox_quick_action_copy?: boolean;
  thinkbox_quick_action_steps?: boolean;
  thinkbox_quick_action_research?: boolean;
  thinkbox_quick_action_clipboard?: boolean;
  thinkbox_allow_no_focus_steal_toggle?: boolean;
  thinkbox_hide_when_main_focus?: boolean;
  thinkbox_remember_last_text?: boolean;
  thinkbox_clear_text_on_send?: boolean;
  thinkbox_status_toast_seconds?: number;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source_name: string;
  rank: number;
}

export interface ThinkBoxMessageRequest {
  text: string;
  mode: "screen_help" | "explain" | "steps" | "extract" | "research";
  toggles?: Record<string, unknown>;
  context?: Record<string, unknown>;
  model_source_id?: string;
  model?: string;
}

export interface SecurityPlan {
  rule_name: string;
  tool_runner_program: string;
  create_rule_command: string;
  status_check_command: string;
}

export interface SecurityStatus {
  rule_name: string;
  tool_runner_program: string;
  exists: boolean;
  enabled: boolean;
  outbound_block: boolean;
  program_matches: boolean;
  confirmed_blocking: boolean;
  detail: string;
}

export interface OllamaStatus {
  installed: boolean;
  healthy: boolean;
  models_count: number;
  last_checked_at: string;
  next_check_in_seconds: number;
  fallback_mode_active: boolean;
  install_prompt_suppressed: boolean;
  install_prompt_suppressed_until?: string | null;
}

export interface SettingsProfile {
  id: string;
  name: string;
  version?: number;
  is_active: boolean;
  payload?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface SettingsRegistryEntry {
  key: string;
  type: string;
  default: unknown;
  category: string;
  scope: string;
  danger: string;
  requires_restart: boolean;
  description: string;
  enum_values?: string[];
}

export interface WorkspaceDef {
  id: string;
  name: string;
  description: string;
  scopes: string[];
  allowed_tools: string[];
  settings: Record<string, unknown>;
  default_profile_id?: string | null;
  default_model_source_id?: string | null;
  default_model?: string | null;
  logging_strictness: "standard" | "strict";
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PolicyValidateResponse {
  ok: boolean;
  errors: string[];
}

export interface PolicyTestResponse {
  allowed: boolean;
  reason: string;
}

export interface RunItem {
  id: string;
  session_id?: string | null;
  mode: string;
  input_hash: string;
  input_text?: string | null;
  model_source_id?: string | null;
  model_name?: string | null;
  created_at?: string;
  duration_ms?: number;
}

export interface RunDetail extends RunItem {
  events: { event_type: string; payload: Record<string, unknown>; created_at: string }[];
}

export interface ArtifactItem {
  id: string;
  run_id?: string | null;
  type: string;
  name: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at?: string;
}

export interface MemoryItem {
  id: string;
  kind: string;
  content: string;
  created_at?: string;
  updated_at?: string;
}

export interface PluginItem {
  id?: string | null;
  name: string;
  type: "builtin" | "local";
  enabled: boolean;
  version?: string | null;
  path?: string | null;
}

const base = "http://127.0.0.1:8000/api/v1";

export function getSessionId(): string {
  const key = "nero_session_id";
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const v = crypto.randomUUID();
  localStorage.setItem(key, v);
  return v;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  headers.set("Content-Type", "application/json");
  headers.set("X-Session-Id", getSessionId());
  const res = await fetch(`${base}${path}`, { ...init, headers });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

export const api = {
  listModels: () => request<ModelOption[]>("/models/options"),
  listRemoteSources: () => request<any[]>("/models/sources"),
  addRemoteSource: (input: RemoteSourceInput) => request<any>("/models/sources", { method: "POST", body: JSON.stringify(input) }),
  testSource: (sourceId: string) => request<{ ok: boolean; detail: string }>(`/models/sources/${sourceId}/test`, { method: "POST" }),
  streamChat: async function* (payload: { source_id: string; model: string; message: string; mode: "chat" | "workflow"; context?: Record<string, unknown> }) {
    const headers = new Headers({ "Content-Type": "application/json", "X-Session-Id": getSessionId() });
    const res = await fetch(`${base}/agent/chat/stream`, { method: "POST", headers, body: JSON.stringify(payload) });
    if (!res.ok || !res.body) throw new Error(await res.text());
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.split("\n").find((x) => x.startsWith("data: "));
        if (!line) continue;
        yield JSON.parse(line.slice(6));
      }
    }
  },
  checkPermission: (permission: PermissionType, path?: string) => request<{ granted: boolean; reason: string }>("/permissions/check", { method: "POST", body: JSON.stringify({ permission, path }) }),
  grantPermission: (payload: { permission: PermissionType; scope: "once" | "session" | "always"; allowed_paths?: string[] }) => request("/permissions/grant", { method: "POST", body: JSON.stringify(payload) }),
  revokePermission: (permission: PermissionType) => request(`/permissions/revoke/${permission}`, { method: "POST" }),
  listPermissions: () => request<any[]>("/permissions/grants"),
  listAudit: () => request<any[]>("/audit/logs"),
  listWorkflows: () => request<WorkflowDef[]>("/workflows"),
  saveWorkflow: (payload: { id?: string; name: string; description: string; definition: Record<string, unknown> }) => request<WorkflowDef>("/workflows", { method: "POST", body: JSON.stringify(payload) }),
  runWorkflow: (id: string, inputs: Record<string, unknown>) => request<{ result: Record<string, unknown> }>(`/workflows/${id}/run`, { method: "POST", body: JSON.stringify({ inputs }) }),
  getSettings: () => request<SettingsDef>("/settings"),
  updateSettings: (payload: Partial<SettingsDef>) => request<SettingsDef>("/settings", { method: "PATCH", body: JSON.stringify(payload) }),
  setSecret: (keyName: string, value: string) => request<{ key_name: string; configured: boolean }>("/settings/secrets", { method: "POST", body: JSON.stringify({ key_name: keyName, value }) }),
  getSecretStatus: (keyName: string) => request<{ key_name: string; configured: boolean }>(`/settings/secrets/${keyName}`),
  getSecurityPlan: () => request<SecurityPlan>("/settings/security/network-lockdown/plan"),
  applySecurityLockdown: () => request<{ launched: boolean; requires_uac: boolean; detail: string }>("/settings/security/network-lockdown/apply", { method: "POST" }),
  getSecurityStatus: () => request<SecurityStatus>("/settings/security/network-lockdown/status"),
  getOllamaStatus: () => request<OllamaStatus>("/ollama/status"),
  promptOllamaInstall: () => request<{ launched: boolean; url: string; detail: string }>("/ollama/install/prompt", { method: "POST" }),
  snoozeOllamaInstallPrompt: () => request<{ status: "ok"; remind_after_minutes: number }>("/ollama/install/remind-later", { method: "POST" }),
  listProfiles: () => request<SettingsProfile[]>("/profiles"),
  getProfile: (id: string) => request<SettingsProfile>(`/profiles/${id}`),
  createProfile: (payload: { name: string; payload?: Record<string, unknown> }) => request<SettingsProfile>("/profiles", { method: "POST", body: JSON.stringify(payload) }),
  updateProfile: (id: string, payload: { name?: string; payload: Record<string, unknown> }) => request<SettingsProfile>(`/profiles/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteProfile: (id: string) => request(`/profiles/${id}`, { method: "DELETE" }),
  applyProfile: (id: string) => request<SettingsProfile>(`/profiles/${id}/activate`, { method: "POST" }),
  revertProfile: (id: string) => request<SettingsProfile>(`/profiles/${id}/rollback`, { method: "POST" }),
  exportProfile: (id: string) => request<SettingsProfile>(`/profiles/${id}/export`, { method: "POST" }),
  importProfile: (payload: { name?: string; payload: Record<string, unknown> }) => request<SettingsProfile>("/profiles/import", { method: "POST", body: JSON.stringify(payload) }),
  duplicateProfile: (id: string, payload: { name?: string }) => request<SettingsProfile>(`/profiles/${id}/duplicate`, { method: "POST", body: JSON.stringify(payload) }),
  resetCategory: (id: string, keys: string[]) => request<SettingsProfile>(`/profiles/${id}/reset-category`, { method: "POST", body: JSON.stringify({ keys }) }),
  getSettingsRegistry: () => request<SettingsRegistryEntry[]>("/settings/registry"),
  testSearchProvider: () => request<any>("/search/test", { method: "POST" }),
  search: (payload: { query: string; num_results?: number; safe?: boolean; manual_payload?: any }) => request<{ status: string; provider: SearchProviderName; results: SearchResult[]; detail: string; manual_instructions?: string }>("/search", { method: "POST", body: JSON.stringify(payload) }),
  manualSearch: (payload: { query: string; json_results?: SearchResult[]; pasted_lines?: string }) => request<{ status: string; provider: SearchProviderName; results: SearchResult[]; detail: string }>("/search/manual", { method: "POST", body: JSON.stringify(payload) })
  ,
  listWorkspaces: () => request<WorkspaceDef[]>("/workspaces"),
  getWorkspace: (id: string) => request<WorkspaceDef>(`/workspaces/${id}`),
  createWorkspace: (payload: { name: string; description?: string; scopes?: string[]; allowed_tools?: string[]; settings?: Record<string, unknown>; default_profile_id?: string | null; default_model_source_id?: string | null; default_model?: string | null; logging_strictness?: "standard" | "strict" }) =>
    request<WorkspaceDef>("/workspaces", { method: "POST", body: JSON.stringify(payload) }),
  updateWorkspace: (id: string, payload: { name?: string; description?: string; scopes?: string[]; allowed_tools?: string[]; settings?: Record<string, unknown>; default_profile_id?: string | null; default_model_source_id?: string | null; default_model?: string | null; logging_strictness?: "standard" | "strict" }) =>
    request<WorkspaceDef>(`/workspaces/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  activateWorkspace: (id: string) => request<WorkspaceDef>(`/workspaces/${id}/activate`, { method: "POST" }),
  deleteWorkspace: (id: string) => request(`/workspaces/${id}`, { method: "DELETE" }),
  validatePolicy: (text: string) => request<PolicyValidateResponse>("/policies/validate", { method: "POST", body: JSON.stringify({ text }) }),
  testPolicy: (payload: { action: string; confirmed?: boolean }) => request<PolicyTestResponse>("/policies/test", { method: "POST", body: JSON.stringify(payload) })
  ,
  listRuns: () => request<RunItem[]>("/runs"),
  getRun: (id: string) => request<RunDetail>(`/runs/${id}`),
  replayRun: (id: string) => request<{ run_id: string; steps: any[] }>(`/runs/${id}/replay`, { method: "POST" })
  ,
  listArtifacts: () => request<ArtifactItem[]>("/artifacts"),
  createArtifact: (payload: { name: string; content: string; type: string; run_id?: string | null; metadata?: Record<string, unknown> }) =>
    request<ArtifactItem>("/artifacts", { method: "POST", body: JSON.stringify(payload) }),
  deleteArtifact: (id: string) => request(`/artifacts/${id}`, { method: "DELETE" })
  ,
  listMemory: () => request<MemoryItem[]>("/memory"),
  createMemory: (payload: { kind: "preference" | "project_fact"; content: string }) => request<MemoryItem>("/memory", { method: "POST", body: JSON.stringify(payload) }),
  updateMemory: (id: string, payload: { content: string }) => request<MemoryItem>(`/memory/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteMemory: (id: string) => request(`/memory/${id}`, { method: "DELETE" })
  ,
  listPlugins: () => request<PluginItem[]>("/plugins"),
  setPluginEnabled: (id: string, enabled: boolean) => request(`/plugins/${id}/enable`, { method: "POST", body: JSON.stringify({ enabled }) })
  ,
  vectorIndex: (payload: { workspace_id: string; items: { path: string; content: string; content_hash: string }[] }) =>
    request("/vector/index", { method: "POST", body: JSON.stringify(payload) }),
  vectorSearch: (payload: { workspace_id: string; query: string; limit?: number }) =>
    request<{ results: { path: string; score: number }[] }>("/vector/search", { method: "POST", body: JSON.stringify(payload) })
  ,
  exportDiagnostics: () => request<{ path: string }>("/diagnostics/export", { method: "POST" })
  ,
  thinkboxMessage: (payload: ThinkBoxMessageRequest) => request<{ run_id: string }>("/thinkbox/message", { method: "POST", body: JSON.stringify(payload) }),
  thinkboxStream: async function* (runId: string) {
    const headers = new Headers({ "X-Session-Id": getSessionId() });
    const res = await fetch(`${base}/thinkbox/stream?run_id=${encodeURIComponent(runId)}`, { method: "GET", headers });
    if (!res.ok || !res.body) throw new Error(await res.text());
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.split("\n").find((x) => x.startsWith("data: "));
        if (!line) continue;
        yield JSON.parse(line.slice(6));
      }
    }
  },
  screenCapture: (payload: { source: "active_window" | "region"; region?: { x: number; y: number; w: number; h: number }; image_data_url?: string }) =>
    request<{ capture_id: string; timestamp: number; thumbnail_data_url?: string }>("/screen/capture", { method: "POST", body: JSON.stringify(payload) }),
  clipboardRead: () => request<{ text: string }>("/clipboard/read", { method: "POST" }),
  clipboardWrite: (text: string) => request("/clipboard/write", { method: "POST", body: JSON.stringify({ text }) }),
  filesSearch: (payload: { path: string; pattern: string; max_results?: number }) =>
    request<{ results: string[] }>("/files/search", { method: "POST", body: JSON.stringify(payload) })
};
