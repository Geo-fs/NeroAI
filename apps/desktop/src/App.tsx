import { useEffect, useMemo, useState } from "react";
import { ChatPage } from "./pages/ChatPage";
import { PermissionsPage } from "./pages/PermissionsPage";
import { WorkflowsPage } from "./pages/WorkflowsPage";
import { AuditPage } from "./pages/AuditPage";
import { SettingsPage } from "./pages/SettingsPage";
import { api, OllamaStatus, SettingsDef, SettingsProfile, WorkspaceDef } from "./api";
import { applyUiSettingsToDocument } from "./uiSettings";

type Tab = "chat" | "permissions" | "workflows" | "audit" | "settings";

export function App() {
  const [tab, setTab] = useState<Tab>("chat");
  const [profiles, setProfiles] = useState<SettingsProfile[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceDef[]>([]);
  const [activeProfile, setActiveProfile] = useState("");
  const [activeWorkspace, setActiveWorkspace] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
  const [showOllamaPrompt, setShowOllamaPrompt] = useState(false);
  const [sessionPromptDismissed, setSessionPromptDismissed] = useState(false);
  const [uiSettings, setUiSettings] = useState<SettingsDef | null>(null);
  const tabs = useMemo(
    () => [
      ["chat", "Chat"],
      ["permissions", "Permissions"],
      ["workflows", "Workflows"],
      ["audit", "Audit"],
      ["settings", "Settings"]
    ] as const,
    []
  );

  async function loadSelectors() {
    const profs = await api.listProfiles();
    const wss = await api.listWorkspaces();
    setProfiles(profs);
    setWorkspaces(wss);
    const p = profs.find((x) => x.is_active) || profs[0];
    const w = wss.find((x) => x.is_active) || wss[0];
    setActiveProfile(p?.id ?? "");
    setActiveWorkspace(w?.id ?? "");
  }

  useEffect(() => {
    loadSelectors().catch(console.error);
  }, []);

  useEffect(() => {
    async function loadUiSettings() {
      const settings = await api.getSettings();
      setUiSettings(settings);
      applyUiSettingsToDocument(settings);
    }
    loadUiSettings().catch(console.error);
    const listener = (event: Event) => {
      const custom = event as CustomEvent<SettingsDef>;
      if (!custom.detail) return;
      setUiSettings(custom.detail);
      applyUiSettingsToDocument(custom.detail);
    };
    window.addEventListener("nero:settings-updated", listener as EventListener);
    return () => window.removeEventListener("nero:settings-updated", listener as EventListener);
  }, []);

  useEffect(() => {
    let timer: number | null = null;
    async function poll() {
      try {
        const status = await api.getOllamaStatus();
        setOllamaStatus(status);
        if (status.healthy) {
          setSessionPromptDismissed(false);
        }
        setShowOllamaPrompt(
          !status.healthy &&
          !status.install_prompt_suppressed &&
          !sessionPromptDismissed
        );
        const interval = Math.max(10, status.next_check_in_seconds || 10) * 1000;
        timer = window.setTimeout(poll, interval);
      } catch {
        timer = window.setTimeout(poll, 10_000);
      }
    }
    poll().catch(console.error);
    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [sessionPromptDismissed]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.ctrlKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function onSelectProfile(id: string) {
    setActiveProfile(id);
    await api.applyProfile(id);
    await loadSelectors();
  }

  async function onSelectWorkspace(id: string) {
    setActiveWorkspace(id);
    await api.activateWorkspace(id);
    await loadSelectors();
  }

  const commands = useMemo(() => {
    const base = [
      { id: "open-settings", label: "Open Settings", action: () => setTab("settings") },
      { id: "open-audit", label: "Open Audit", action: () => setTab("audit") },
      { id: "open-workflows", label: "Open Workflows", action: () => setTab("workflows") },
      { id: "open-permissions", label: "Open Permissions", action: () => setTab("permissions") }
    ];
    const profileCmds = profiles.map((p) => ({
      id: `profile-${p.id}`,
      label: `Switch Profile: ${p.name}`,
      action: () => onSelectProfile(p.id)
    }));
    const workspaceCmds = workspaces.map((w) => ({
      id: `workspace-${w.id}`,
      label: `Switch Workspace: ${w.name}`,
      action: () => onSelectWorkspace(w.id)
    }));
    return [...base, ...profileCmds, ...workspaceCmds];
  }, [profiles, workspaces]);

  const filteredCommands = commands.filter((c) => c.label.toLowerCase().includes(paletteQuery.toLowerCase()));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>NeroAI</h1>
        {tabs.map(([id, label]) => (
          <button key={id} className={`nav-btn ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </aside>
      <main className="main">
        {showOllamaPrompt && (
          <div className="card" style={{ border: "1px solid #f59e0b" }}>
            <h3>Ollama Not Available</h3>
            <p className="small">
              Local Ollama is not reachable. NeroAI will use web-search fallback mode until Ollama is installed and detected.
            </p>
            <div className="row">
              <button
                onClick={async () => {
                  const res = await api.promptOllamaInstall();
                  await window.neroDesktop?.openExternal?.(res.url);
                }}
              >
                Install Ollama
              </button>
              <button
                className="secondary"
                onClick={async () => {
                  await api.snoozeOllamaInstallPrompt();
                  setSessionPromptDismissed(true);
                  setShowOllamaPrompt(false);
                }}
              >
                Remind Me Later
              </button>
              <button className="secondary" onClick={() => { setSessionPromptDismissed(true); setShowOllamaPrompt(false); }}>
                Continue with Web Search
              </button>
            </div>
            {ollamaStatus && (
              <p className="small">
                Last check: {ollamaStatus.last_checked_at} | Models: {ollamaStatus.models_count}
              </p>
            )}
          </div>
        )}
        {uiSettings?.ui_show_topbar !== false && (
        <div className={`topbar card ${uiSettings?.ui_topbar_compact ? "compact" : ""}`}>
          <div className="row">
            <label>Workspace</label>
            <select value={activeWorkspace} onChange={(e) => onSelectWorkspace(e.target.value)}>
              {workspaces.map((w) => <option key={w.id} value={w.id}>{w.name} {w.is_active ? "(Active)" : ""}</option>)}
            </select>
            <label>Profile</label>
            <select value={activeProfile} onChange={(e) => onSelectProfile(e.target.value)}>
              {profiles.map((p) => <option key={p.id} value={p.id}>{p.name} {p.is_active ? "(Active)" : ""}</option>)}
            </select>
            <button className="secondary" onClick={() => window.neroDesktop?.toggleThinkBox().catch(console.error)}>Think Box</button>
            <button className="secondary" onClick={() => loadSelectors().catch(console.error)}>Refresh</button>
          </div>
        </div>
        )}
        {tab === "chat" && <ChatPage settings={uiSettings ?? undefined} />}
        {tab === "permissions" && <PermissionsPage />}
        {tab === "workflows" && <WorkflowsPage />}
        {tab === "audit" && <AuditPage />}
        {tab === "settings" && <SettingsPage />}

        {paletteOpen && (
          <div className="palette">
            <div className="palette-box card">
              <input
                autoFocus
                placeholder="Type a command"
                value={paletteQuery}
                onChange={(e) => setPaletteQuery(e.target.value)}
              />
              <div style={{ marginTop: 8 }}>
                {filteredCommands.slice(0, Math.max(1, uiSettings?.ui_palette_max_results ?? 12)).map((cmd) => (
                  <button
                    key={cmd.id}
                    className="nav-btn"
                    onClick={() => {
                      cmd.action();
                      setPaletteOpen(false);
                      setPaletteQuery("");
                    }}
                  >
                    {cmd.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
