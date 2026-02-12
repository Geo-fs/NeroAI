import { useEffect, useState } from "react";
import { api, PluginItem, SecurityPlan, SecurityStatus, SettingsDef, SettingsProfile, SettingsRegistryEntry, WorkspaceDef } from "../api";

const baseCategories = ["General", "Models", "Agent Runtime", "Security", "Tools", "Search", "Workflows", "Logging", "UI", "Advanced"];

const defaults: SettingsDef = {
  safe_mode_default: true,
  privacy_mode: true,
  redaction_enabled: true,
  allow_query_text_logging: false,
  verbose_logging: false,
  policy_rules: "",
  search_provider: "duckduckgo_html",
  local_browser_enabled: false,
  local_browser_headed: true,
  local_browser_engine: "chrome",
  max_tool_calls_per_message: 3,
  max_tool_calls_per_minute: 15,
  max_files_read_per_run: 20,
  max_bytes_read_per_run: 5_000_000,
  max_runtime_seconds: 120,
  write_preview_default: true,
  quarantine_mode: true,
  use_saved_memory: false,
  reviewer_enabled: false,
  reviewer_strictness: "standard",
  dry_run_mode: "ask",
  thinkbox_enabled: true,
  thinkbox_hotkey: "Control+Alt+Space",
  thinkbox_position: "bottom-right",
  thinkbox_size_percent: 20,
  thinkbox_auto_hide_seconds: 30,
  thinkbox_pin_default: false,
  thinkbox_no_focus_steal: false,
  thinkbox_capture_default: "active_window",
  thinkbox_awareness_default: false,
  thinkbox_awareness_minutes: 10,
  thinkbox_awareness_interval_seconds: 0,
  thinkbox_store_screenshots: false,
  thinkbox_store_thumbnail: false,
  ollama_required_for_local_chat: true,
  ollama_check_interval_seconds: 10,
  ollama_install_prompt_enabled: true,
  ollama_remind_later_minutes: 60,
  ollama_fallback_mode: "search_answer",
};

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsDef>(defaults);
  const [status, setStatus] = useState("");
  const [secretName, setSecretName] = useState("search:api_key");
  const [secretValue, setSecretValue] = useState("");
  const [testStatus, setTestStatus] = useState("");
  const [securityPlan, setSecurityPlan] = useState<SecurityPlan | null>(null);
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
  const [securityMsg, setSecurityMsg] = useState("");
  const [profiles, setProfiles] = useState<SettingsProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState("");
  const [profileName, setProfileName] = useState("Default");
  const [profileStatus, setProfileStatus] = useState("");
  const [searchText, setSearchText] = useState("");
  const [category, setCategory] = useState("General");
  const [profileJson, setProfileJson] = useState("");
  const [registry, setRegistry] = useState<SettingsRegistryEntry[]>([]);
  const [profilePayload, setProfilePayload] = useState<Record<string, unknown>>({});
  const [workspaces, setWorkspaces] = useState<WorkspaceDef[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDesc, setWorkspaceDesc] = useState("");
  const [workspaceScopes, setWorkspaceScopes] = useState("");
  const [workspaceTools, setWorkspaceTools] = useState("");
  const [workspaceStatus, setWorkspaceStatus] = useState("");
  const [workspaceLimits, setWorkspaceLimits] = useState({
    max_tool_calls_per_message: 3,
    max_tool_calls_per_minute: 15,
    max_files_read_per_run: 20,
    max_bytes_read_per_run: 5_000_000,
    max_runtime_seconds: 120
  });
  const [workspaceLogging, setWorkspaceLogging] = useState<"standard" | "strict">("standard");
  const [policyStatus, setPolicyStatus] = useState("");
  const [policyTestAction, setPolicyTestAction] = useState("tool.file_write");
  const [policyTestResult, setPolicyTestResult] = useState("");
  const [memoryItems, setMemoryItems] = useState<any[]>([]);
  const [memoryKind, setMemoryKind] = useState<"preference" | "project_fact">("preference");
  const [memoryContent, setMemoryContent] = useState("");
  const [plugins, setPlugins] = useState<PluginItem[]>([]);
  const [diagStatus, setDiagStatus] = useState("");
  const [thinkboxHotkeyStatus, setThinkboxHotkeyStatus] = useState("");

  function safeJson(value: string): Record<string, unknown> {
    try {
      return JSON.parse(value || "{}");
    } catch (err) {
      setProfileStatus("Invalid JSON.");
      return {};
    }
  }

  async function load() {
    setSettings(await api.getSettings());
    setRegistry(await api.getSettingsRegistry());
    const list = await api.listProfiles();
    setProfiles(list);
    const work = await api.listWorkspaces();
    setWorkspaces(work);
    const activeWs = work.find((w) => w.is_active) || work[0];
    if (activeWs) {
      setActiveWorkspaceId(activeWs.id);
      setWorkspaceName(activeWs.name);
      setWorkspaceDesc(activeWs.description || "");
      setWorkspaceScopes((activeWs.scopes || []).join(";"));
      setWorkspaceTools((activeWs.allowed_tools || []).join(";"));
      const wsSettings = activeWs.settings || {};
      setWorkspaceLimits({
        max_tool_calls_per_message: Number(wsSettings.max_tool_calls_per_message ?? 3),
        max_tool_calls_per_minute: Number(wsSettings.max_tool_calls_per_minute ?? 15),
        max_files_read_per_run: Number(wsSettings.max_files_read_per_run ?? 20),
        max_bytes_read_per_run: Number(wsSettings.max_bytes_read_per_run ?? 5_000_000),
        max_runtime_seconds: Number(wsSettings.max_runtime_seconds ?? 120)
      });
      setWorkspaceLogging(activeWs.logging_strictness || "standard");
    }
    const active = list.find((p) => p.is_active) || list[0];
    if (active) {
      setActiveProfileId(active.id);
      setProfileName(active.name);
      const details = await api.getProfile(active.id);
      setProfilePayload(details.payload ?? {});
      setProfileJson(JSON.stringify(details.payload ?? {}, null, 2));
    }
    setMemoryItems(await api.listMemory());
    setPlugins(await api.listPlugins());
  }

  useEffect(() => {
    load().catch((e) => setStatus(String(e)));
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("nero_settings_last_category");
    if (saved) setCategory(saved);
  }, []);

  useEffect(() => {
    if (settings.ui_settings_remember_last_category) {
      localStorage.setItem("nero_settings_last_category", category);
    }
  }, [category, settings.ui_settings_remember_last_category]);

  async function save() {
    const updated = await api.updateSettings(settings);
    setSettings(updated);
    window.dispatchEvent(new CustomEvent("nero:settings-updated", { detail: updated }));
    if (window.neroDesktop) {
      const result = await window.neroDesktop.updateThinkBoxHotkey(updated.thinkbox_hotkey, updated.thinkbox_enabled);
      setThinkboxHotkeyStatus(result.ok ? `Hotkey active: ${result.hotkey}` : (result.error || "Failed to register Think Box hotkey."));
    }
    setStatus("Settings saved.");
  }

  async function testProvider() {
    const result = await api.testSearchProvider();
    setTestStatus(`${result.status}: ${result.detail ?? "ok"} (${result.provider})`);
  }

  async function saveSecret() {
    await api.setSecret(secretName, secretValue);
    setSecretValue("");
    setStatus("Secret stored.");
  }

  function filteredCategories() {
    const dynamic = Array.from(new Set(registry.map((r) => r.category)));
    const all = [...baseCategories, ...dynamic.filter((x) => !baseCategories.includes(x))];
    if (!searchText.trim()) return all;
    const q = searchText.toLowerCase();
    const matches = registry.filter((r) => r.key.toLowerCase().includes(q) || (r.description || "").toLowerCase().includes(q));
    const matchedCategories = new Set(matches.map((m) => m.category));
    return all.filter((c) => matchedCategories.has(c));
  }

  async function refreshProfile(id: string) {
    const profile = await api.getProfile(id);
    setProfileName(profile.name);
    setProfilePayload(profile.payload ?? {});
    setProfileJson(JSON.stringify(profile.payload ?? {}, null, 2));
  }

  async function createProfile() {
    const p = await api.createProfile({ name: profileName, payload: profilePayload });
    setProfileStatus("Profile created.");
    await load();
    setActiveProfileId(p.id);
  }

  async function duplicateProfile() {
    if (!activeProfileId) return;
    const p = await api.duplicateProfile(activeProfileId, { name: profileName + " Copy" });
    setProfileStatus("Profile duplicated.");
    await load();
    setActiveProfileId(p.id);
  }

  async function renameProfile() {
    if (!activeProfileId) return;
    await api.updateProfile(activeProfileId, { name: profileName, payload: profilePayload });
    setProfileStatus("Profile renamed.");
    await load();
  }

  async function deleteProfile() {
    if (!activeProfileId) return;
    await api.deleteProfile(activeProfileId);
    setProfileStatus("Profile deleted.");
    await load();
  }

  async function applyProfile() {
    if (!activeProfileId) return;
    await api.applyProfile(activeProfileId);
    setProfileStatus("Profile applied.");
    await load();
  }

  async function revertProfile() {
    if (!activeProfileId) return;
    await api.revertProfile(activeProfileId);
    await refreshProfile(activeProfileId);
    setProfileStatus("Reverted to last-known-good profile data.");
  }

  async function exportProfile() {
    if (!activeProfileId) return;
    const data = await api.exportProfile(activeProfileId);
    setProfileJson(JSON.stringify(data.payload ?? {}, null, 2));
    setProfileStatus("Exported profile JSON.");
  }

  async function importProfile() {
    const payload = safeJson(profileJson);
    const p = await api.importProfile({ name: profileName || "Imported", payload });
    setProfileStatus("Imported profile.");
    await load();
    setActiveProfileId(p.id);
  }

  async function applyEdits() {
    if (!activeProfileId) return;
    await api.updateProfile(activeProfileId, { name: profileName, payload: profilePayload });
    await api.applyProfile(activeProfileId);
    const synced = await api.getSettings();
    setSettings(synced);
    window.dispatchEvent(new CustomEvent("nero:settings-updated", { detail: synced }));
    const hotkey = String(profilePayload.thinkbox_hotkey ?? settings.thinkbox_hotkey ?? "Control+Alt+Space");
    const enabled = Boolean(profilePayload.thinkbox_enabled ?? settings.thinkbox_enabled ?? true);
    if (window.neroDesktop) {
      const result = await window.neroDesktop.updateThinkBoxHotkey(hotkey, enabled);
      setThinkboxHotkeyStatus(result.ok ? `Hotkey active: ${result.hotkey}` : (result.error || "Failed to register Think Box hotkey."));
    }
    setProfileStatus("Profile updated.");
    await load();
  }

  async function revertEdits() {
    if (!activeProfileId) return;
    await refreshProfile(activeProfileId);
    setProfileStatus("Reverted unsaved edits.");
  }

  async function resetCategory() {
    if (!activeProfileId) return;
    const keys = registry.filter((r) => r.category === category).map((r) => r.key);
    await api.resetCategory(activeProfileId, keys);
    await refreshProfile(activeProfileId);
    setProfileStatus("Category reset to defaults.");
  }

  function updateSetting(key: string, value: unknown) {
    setProfilePayload((prev) => ({ ...prev, [key]: value }));
  }

  async function refreshWorkspace(id: string) {
    const ws = await api.getWorkspace(id);
    setActiveWorkspaceId(ws.id);
    setWorkspaceName(ws.name);
    setWorkspaceDesc(ws.description || "");
    setWorkspaceScopes((ws.scopes || []).join(";"));
    setWorkspaceTools((ws.allowed_tools || []).join(";"));
    const wsSettings = ws.settings || {};
    setWorkspaceLimits({
      max_tool_calls_per_message: Number(wsSettings.max_tool_calls_per_message ?? 3),
      max_tool_calls_per_minute: Number(wsSettings.max_tool_calls_per_minute ?? 15),
      max_files_read_per_run: Number(wsSettings.max_files_read_per_run ?? 20),
      max_bytes_read_per_run: Number(wsSettings.max_bytes_read_per_run ?? 5_000_000),
      max_runtime_seconds: Number(wsSettings.max_runtime_seconds ?? 120)
    });
    setWorkspaceLogging(ws.logging_strictness || "standard");
  }

  async function createWorkspace() {
    const ws = await api.createWorkspace({
      name: workspaceName || "New Workspace",
      description: workspaceDesc,
      scopes: workspaceScopes.split(";").map((s) => s.trim()).filter(Boolean),
      allowed_tools: workspaceTools.split(";").map((s) => s.trim()).filter(Boolean),
      logging_strictness: workspaceLogging,
      settings: workspaceLimits
    });
    setWorkspaceStatus("Workspace created.");
    await load();
    setActiveWorkspaceId(ws.id);
  }

  async function updateWorkspace() {
    if (!activeWorkspaceId) return;
    await api.updateWorkspace(activeWorkspaceId, {
      name: workspaceName,
      description: workspaceDesc,
      scopes: workspaceScopes.split(";").map((s) => s.trim()).filter(Boolean),
      allowed_tools: workspaceTools.split(";").map((s) => s.trim()).filter(Boolean),
      logging_strictness: workspaceLogging,
      settings: workspaceLimits
    });
    setWorkspaceStatus("Workspace updated.");
    await load();
  }

  async function activateWorkspace() {
    if (!activeWorkspaceId) return;
    await api.activateWorkspace(activeWorkspaceId);
    setWorkspaceStatus("Workspace activated.");
    await load();
  }

  async function deleteWorkspace() {
    if (!activeWorkspaceId) return;
    await api.deleteWorkspace(activeWorkspaceId);
    setWorkspaceStatus("Workspace deleted.");
    await load();
  }

  async function addMemory() {
    if (!memoryContent.trim()) return;
    await api.createMemory({ kind: memoryKind, content: memoryContent });
    setMemoryContent("");
    setMemoryItems(await api.listMemory());
  }

  async function deleteMemory(id: string) {
    await api.deleteMemory(id);
    setMemoryItems(await api.listMemory());
  }

  async function exportDiagnostics() {
    const res = await api.exportDiagnostics();
    setDiagStatus(`Diagnostics exported: ${res.path}`);
  }

  function renderField(item: SettingsRegistryEntry) {
    const value = profilePayload[item.key] ?? item.default;
    if (item.type === "bool") {
      return (
        <label>
          <input type="checkbox" checked={Boolean(value)} onChange={(e) => updateSetting(item.key, e.target.checked)} /> {item.description}
        </label>
      );
    }
    if (item.type === "int" || item.type === "float") {
      return (
        <input
          type="number"
          value={Number(value)}
          onChange={(e) => updateSetting(item.key, item.type === "int" ? parseInt(e.target.value, 10) : parseFloat(e.target.value))}
        />
      );
    }
    if (item.type === "enum" && item.enum_values) {
      return (
        <select value={String(value)} onChange={(e) => updateSetting(item.key, e.target.value)}>
          {item.enum_values.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
      );
    }
    return (
      <input value={String(value ?? "")} onChange={(e) => updateSetting(item.key, e.target.value)} />
    );
  }

  async function validatePolicy() {
    const text = String(profilePayload.policy_rules ?? "");
    const res = await api.validatePolicy(text);
    if (res.ok) {
      setPolicyStatus("Policy syntax OK.");
    } else {
      setPolicyStatus(res.errors.join(" | "));
    }
  }

  async function testPolicy() {
    const res = await api.testPolicy({ action: policyTestAction, confirmed: false });
    setPolicyTestResult(`${res.allowed ? "ALLOWED" : "DENIED"}: ${res.reason}`);
  }

  const visibleItems = registry
    .filter((r) => r.category === category)
    .filter((r) => (category === "Security" ? r.key !== "policy_rules" : true))
    .filter((r) => {
      if (!searchText.trim()) return true;
      const q = searchText.toLowerCase();
      return r.key.toLowerCase().includes(q) || (r.description || "").toLowerCase().includes(q);
    });

  const uiGroups: Array<{ title: string; keys: SettingsRegistryEntry[] }> = [
    {
      title: "Main App UI",
      keys: visibleItems.filter((item) => item.key.startsWith("ui_") && !["ui_reduce_motion", "ui_high_contrast", "ui_focus_ring_enabled", "ui_focus_ring_thickness", "ui_font_scale_percent"].includes(item.key)),
    },
    {
      title: "Think Box",
      keys: visibleItems.filter((item) => item.key.startsWith("thinkbox_")),
    },
    {
      title: "Accessibility",
      keys: visibleItems.filter((item) => ["ui_reduce_motion", "ui_high_contrast", "ui_focus_ring_enabled", "ui_focus_ring_thickness", "ui_font_scale_percent"].includes(item.key)),
    },
    {
      title: "Advanced UI",
      keys: visibleItems.filter((item) => ["ui_settings_show_advanced_badges", "ui_settings_remember_last_category", "ui_palette_blur_background", "ui_palette_max_results"].includes(item.key)),
    },
  ];

  async function loadSecurityPlan() {
    const plan = await api.getSecurityPlan();
    setSecurityPlan(plan);
    setSecurityMsg("Review planned firewall changes below before applying.");
  }

  async function applySecurityLockdown() {
    const result = await api.applySecurityLockdown();
    setSecurityMsg(result.detail);
  }

  async function checkSecurityStatus() {
    const result = await api.getSecurityStatus();
    setSecurityStatus(result);
    if (result.confirmed_blocking) {
      setSecurityMsg("Confirmed: outbound block rule exists, enabled, outbound=block, and program matches.");
    } else {
      setSecurityMsg("Not confirmed yet. Network blocking is not assumed until status confirms all checks.");
    }
  }

  return (
    <div className="settings-shell">
      <aside className="settings-sidebar card">
        <h3>Settings</h3>
        <input value={searchText} onChange={(e) => setSearchText(e.target.value)} placeholder="Search settings" />
        <div style={{ marginTop: 10 }}>
          {filteredCategories().map((c) => (
            <button key={c} className={`nav-btn ${category === c ? "active" : ""}`} onClick={() => setCategory(c)}>
              {c}
            </button>
          ))}
        </div>
      </aside>

      <section>
      <div className="card">
        <h3>Profiles</h3>
        <div className="row">
          <select value={activeProfileId} onChange={(e) => { setActiveProfileId(e.target.value); refreshProfile(e.target.value).catch(console.error); }}>
            {profiles.map((p) => <option key={p.id} value={p.id}>{p.name} {p.is_active ? "(Active)" : ""}</option>)}
          </select>
          <input value={profileName} onChange={(e) => setProfileName(e.target.value)} placeholder="Profile name" />
          <button onClick={createProfile}>Create</button>
          <button onClick={duplicateProfile}>Duplicate</button>
          <button onClick={renameProfile}>Rename</button>
          <button className="danger" onClick={deleteProfile}>Delete</button>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button onClick={applyProfile}>Apply</button>
          <button className="secondary" onClick={revertProfile}>Rollback</button>
          <button onClick={applyEdits}>Apply Edits</button>
          <button className="secondary" onClick={revertEdits}>Revert Edits</button>
          <button onClick={exportProfile}>Export JSON</button>
          <button onClick={importProfile}>Import JSON</button>
          <button onClick={resetCategory}>Reset Category</button>
        </div>
        <textarea style={{ width: "100%", minHeight: 120, marginTop: 8 }} value={profileJson} onChange={(e) => setProfileJson(e.target.value)} placeholder="JSON import/export" />
        {profileStatus && <p className="small">{profileStatus}</p>}
      </div>

      <div className="card">
        <h3>{category}</h3>
        {category !== "UI" && visibleItems.map((item) => (
          <div key={item.key} className="audit-row">
            <div><strong>{item.key}</strong> <span className="small">({item.type}, {item.scope})</span></div>
            {settings.ui_settings_show_descriptions !== false && <div className="small">{item.description}</div>}
            <div className="row" style={{ marginTop: 6 }}>
              {renderField(item)}
              {item.requires_restart && <span className="small">Requires restart</span>}
              {settings.ui_settings_show_advanced_badges !== false && item.danger !== "normal" && <span className="small">Danger: {item.danger}</span>}
            </div>
          </div>
        ))}
        {category === "UI" && uiGroups.map((group) => (
          <div key={group.title} style={{ marginBottom: 12 }}>
            <h4 style={{ margin: "10px 0" }}>{group.title}</h4>
            {group.keys.map((item) => (
              <div key={item.key} className="audit-row">
                <div><strong>{item.key}</strong> <span className="small">({item.type}, {item.scope})</span></div>
                {settings.ui_settings_show_descriptions !== false && <div className="small">{item.description}</div>}
                <div className="row" style={{ marginTop: 6 }}>
                  {renderField(item)}
                  {item.requires_restart && <span className="small">Requires restart</span>}
                  {settings.ui_settings_show_advanced_badges !== false && item.danger !== "normal" && <span className="small">Danger: {item.danger}</span>}
                </div>
              </div>
            ))}
          </div>
        ))}
        {visibleItems.length === 0 && (
          <p className="small">No settings match this category and search filter.</p>
        )}
      </div>

      {category === "General" && (
        <div className="card">
          <h3>Workspaces</h3>
          <div className="row">
            <select value={activeWorkspaceId} onChange={(e) => refreshWorkspace(e.target.value).catch(console.error)}>
              {workspaces.map((w) => <option key={w.id} value={w.id}>{w.name} {w.is_active ? "(Active)" : ""}</option>)}
            </select>
            <input value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} placeholder="Workspace name" />
            <button onClick={createWorkspace}>Create</button>
            <button onClick={updateWorkspace}>Save</button>
            <button className="secondary" onClick={activateWorkspace}>Activate</button>
            <button className="danger" onClick={deleteWorkspace}>Delete</button>
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <input style={{ minWidth: 280 }} value={workspaceDesc} onChange={(e) => setWorkspaceDesc(e.target.value)} placeholder="Description" />
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <input style={{ minWidth: 380 }} value={workspaceScopes} onChange={(e) => setWorkspaceScopes(e.target.value)} placeholder="Allowed folders (separate with ;)" />
            <input style={{ minWidth: 320 }} value={workspaceTools} onChange={(e) => setWorkspaceTools(e.target.value)} placeholder="Allowed tools (separate with ;)" />
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <label>Logging strictness</label>
            <select value={workspaceLogging} onChange={(e) => setWorkspaceLogging(e.target.value as "standard" | "strict")}>
              <option value="standard">standard</option>
              <option value="strict">strict</option>
            </select>
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <label>Max tool calls/message</label>
            <input type="number" value={workspaceLimits.max_tool_calls_per_message} onChange={(e) => setWorkspaceLimits((prev) => ({ ...prev, max_tool_calls_per_message: parseInt(e.target.value, 10) }))} />
            <label>Max tool calls/min</label>
            <input type="number" value={workspaceLimits.max_tool_calls_per_minute} onChange={(e) => setWorkspaceLimits((prev) => ({ ...prev, max_tool_calls_per_minute: parseInt(e.target.value, 10) }))} />
            <label>Max files/read</label>
            <input type="number" value={workspaceLimits.max_files_read_per_run} onChange={(e) => setWorkspaceLimits((prev) => ({ ...prev, max_files_read_per_run: parseInt(e.target.value, 10) }))} />
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <label>Max bytes/read</label>
            <input type="number" value={workspaceLimits.max_bytes_read_per_run} onChange={(e) => setWorkspaceLimits((prev) => ({ ...prev, max_bytes_read_per_run: parseInt(e.target.value, 10) }))} />
            <label>Max runtime (s)</label>
            <input type="number" value={workspaceLimits.max_runtime_seconds} onChange={(e) => setWorkspaceLimits((prev) => ({ ...prev, max_runtime_seconds: parseInt(e.target.value, 10) }))} />
          </div>
          {workspaceStatus && <p className="small">{workspaceStatus}</p>}
        </div>
      )}

      {category === "Tools" && (
      <div className="card">
        <h3>Plugins</h3>
        <div style={{ marginTop: 8 }}>
          {plugins.map((p, idx) => (
            <div key={idx} className="audit-row">
              <div><strong>{p.name}</strong> ({p.type}) {p.version ? `v${p.version}` : ""}</div>
              <div className="small">{p.path ?? ""}</div>
              {p.type === "local" && (
                <button className="secondary" onClick={() => api.setPluginEnabled(p.id as string, !p.enabled).then(load)}>
                  {p.enabled ? "Disable" : "Enable"}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
      )}

      {category === "Search" && (
        <div className="card">
          <h3>Search Provider Test</h3>
          <button onClick={testProvider}>Test provider</button>
          {testStatus && <p className="small">{testStatus}</p>}
        </div>
      )}

      {category === "Security" && (
      <div className="card">
        <h3>Security Hardening</h3>
        <div className="row">
          <button className="secondary" onClick={loadSecurityPlan}>Show Planned Changes</button>
          <button className="danger" onClick={applySecurityLockdown}>Lock Down Tool Runner Network</button>
          <button onClick={checkSecurityStatus}>Check Status</button>
        </div>
        <p className="small">Applying lock down will trigger a Windows UAC prompt for admin approval.</p>
        {securityPlan && (
          <div className="small">
            <div><strong>Rule:</strong> {securityPlan.rule_name}</div>
            <div><strong>Program:</strong> {securityPlan.tool_runner_program}</div>
            <div><strong>Create:</strong> <span className="code">{securityPlan.create_rule_command}</span></div>
            <div><strong>Status Check:</strong> <span className="code">{securityPlan.status_check_command}</span></div>
          </div>
        )}
        {securityStatus && (
          <div className="small">
            <div>exists={String(securityStatus.exists)} enabled={String(securityStatus.enabled)} outbound_block={String(securityStatus.outbound_block)} program_matches={String(securityStatus.program_matches)}</div>
            <div><strong>confirmed_blocking:</strong> {String(securityStatus.confirmed_blocking)}</div>
            <div>{securityStatus.detail}</div>
          </div>
        )}
        {securityMsg && <p className="small">{securityMsg}</p>}
      </div>
      )}

      {category === "Security" && (
      <div className="card">
        <h3>Policy Rules</h3>
        <textarea
          style={{ width: "100%", minHeight: 140 }}
          value={String(profilePayload.policy_rules ?? "")}
          onChange={(e) => updateSetting("policy_rules", e.target.value)}
          placeholder={"deny(tool.file_write) unless confirm\nallow(web.search) only in profile=Research\nmax_tool_calls_per_message = 3 in profile=LockedDown"}
        />
        <div className="row" style={{ marginTop: 8 }}>
          <button onClick={validatePolicy}>Validate</button>
          <input value={policyTestAction} onChange={(e) => setPolicyTestAction(e.target.value)} placeholder="Action, e.g. tool.file_write" style={{ minWidth: 260 }} />
          <button className="secondary" onClick={testPolicy}>Test Policy</button>
        </div>
        {policyStatus && <p className="small">{policyStatus}</p>}
        {policyTestResult && <p className="small">{policyTestResult}</p>}
      </div>
      )}

      {category === "Advanced" && (
      <div className="card">
        <h3>Secure Secrets</h3>
        <div className="row">
          <input value={secretName} onChange={(e) => setSecretName(e.target.value)} placeholder="Secret key name" />
          <input value={secretValue} onChange={(e) => setSecretValue(e.target.value)} placeholder="Secret value" style={{ minWidth: 320 }} />
          <button onClick={saveSecret}>Store Secret</button>
          <button className="secondary" onClick={save}>Save Settings</button>
        </div>
        {status && <p className="small">{status}</p>}
      </div>
      )}
      {category === "Advanced" && (
      <div className="card">
        <h3>Memory</h3>
        <div className="row">
          <select value={memoryKind} onChange={(e) => setMemoryKind(e.target.value as "preference" | "project_fact")}>
            <option value="preference">preference</option>
            <option value="project_fact">project_fact</option>
          </select>
          <input value={memoryContent} onChange={(e) => setMemoryContent(e.target.value)} placeholder="Memory content" style={{ minWidth: 320 }} />
          <button onClick={addMemory}>Save</button>
        </div>
        <div style={{ marginTop: 8 }}>
          {memoryItems.map((item) => (
            <div key={item.id} className="audit-row">
              <div><strong>{item.kind}</strong></div>
              <div className="small">{item.content}</div>
              <button className="secondary" onClick={() => deleteMemory(item.id)}>Delete</button>
            </div>
          ))}
        </div>
      </div>
      )}
      {category === "Advanced" && (
      <div className="card">
        <h3>Diagnostics Bundle</h3>
        <div className="row">
          <button onClick={exportDiagnostics}>Export diagnostics</button>
        </div>
        {diagStatus && <p className="small">{diagStatus}</p>}
      </div>
      )}
      {category !== "Search" && category !== "Logging" && category !== "Security" && category !== "Advanced" && visibleItems.length === 0 && (
        <div className="card">
          <h3>{category}</h3>
          <p className="small">This category is reserved for future settings. Profiles can already store values for it.</p>
        </div>
      )}
      {category === "UI" && (
        <div className="card">
          <h3>UI Apply</h3>
          <p className="small">Apply updates profile overrides and synchronizes global runtime settings from the active profile.</p>
          <div className="row">
            <button onClick={applyEdits}>Apply UI Settings</button>
            <button className="secondary" onClick={revertEdits}>Revert UI Edits</button>
            <button onClick={save}>Save Typed Global Settings</button>
          </div>
          {thinkboxHotkeyStatus && <p className="small">{thinkboxHotkeyStatus}</p>}
        </div>
      )}
      </section>
    </div>
  );
}
