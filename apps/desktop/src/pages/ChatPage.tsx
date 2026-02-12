import { KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, MessageItem, ModelOption, PermissionType, SettingsDef } from "../api";

export function ChatPage({ settings }: { settings?: SettingsDef }) {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [sourceId, setSourceId] = useState("");
  const [model, setModel] = useState("");
  const [text, setText] = useState("Explain how permission-based tool execution works.");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [safeMode, setSafeMode] = useState(true);
  const [busy, setBusy] = useState(false);
  const [pendingPermission, setPendingPermission] = useState<PermissionType | "">("");
  const [pathScope, setPathScope] = useState("C:\\Users\\mike\\OneDrive\\Desktop\\AIs.etc\\NeroAI");

  const [newSourceName, setNewSourceName] = useState("Remote Ollama");
  const [newSourceBase, setNewSourceBase] = useState("http://localhost:11434");
  const [newSourceAuth, setNewSourceAuth] = useState("");
  const [sourceStatus, setSourceStatus] = useState("");
  const [manualQuery, setManualQuery] = useState("");
  const [manualInput, setManualInput] = useState("");
  const [lastRunId, setLastRunId] = useState("");
  const chatLogRef = useRef<HTMLDivElement | null>(null);

  async function refreshModels() {
    const data = await api.listModels();
    setModels(data);
    if (data.length && !sourceId) {
      setSourceId(data[0].source_id);
      setModel(data[0].model);
    }
  }

  useEffect(() => {
    Promise.all([refreshModels(), api.getSettings()])
      .then(([, cfg]) => setSafeMode(cfg.safe_mode_default))
      .catch((e) => setMessages((m) => [...m, { role: "system", content: String(e) }]));
  }, []);

  useEffect(() => {
    if (settings?.ui_chat_autoscroll !== false && chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [messages, settings?.ui_chat_autoscroll]);

  const filtered = useMemo(() => models.filter((m) => m.source_id === sourceId), [models, sourceId]);

  async function addSource() {
    await api.addRemoteSource({ name: newSourceName, base_url: newSourceBase, auth_token: newSourceAuth || undefined });
    setSourceStatus("Source added.");
    await refreshModels();
  }

  async function testSource() {
    if (!sourceId) return;
    const result = await api.testSource(sourceId);
    setSourceStatus(result.detail);
  }

  async function grant(scope: "once" | "session" | "always") {
    if (!pendingPermission) return;
    await api.grantPermission({ permission: pendingPermission, scope, allowed_paths: pathScope ? [pathScope] : [] });
    setMessages((m) => [...m, { role: "system", content: `Granted ${pendingPermission} (${scope}).` }]);
    setPendingPermission("");
  }

  async function send() {
    if (!sourceId || !model || !text.trim()) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    try {
      for await (const event of api.streamChat({ source_id: sourceId, model, message: text, mode: "chat", context: { safe_mode: safeMode } })) {
        if (event.type === "token") {
          setMessages((m) => {
            const next = [...m];
            next[next.length - 1] = { role: "assistant", content: (next[next.length - 1]?.content ?? "") + event.content };
            return next;
          });
        }
        if (event.type === "run_started") {
          setLastRunId(event.run_id ?? "");
        }
        if (event.type === "permission_required") {
          setPendingPermission(event.permission);
          setMessages((m) => [...m, { role: "system", content: `Permission required: ${event.permission}` }]);
        }
        if (event.type === "manual_search_required") {
          setManualQuery(event.query ?? "");
          setMessages((m) => [...m, { role: "system", content: event.instructions ?? "Manual search input required." }]);
        }
        if (event.type === "error") {
          setMessages((m) => [...m, { role: "system", content: event.detail }]);
        }
        if (event.type === "fallback_mode") {
          setMessages((m) => [...m, { role: "system", content: `Fallback mode: ${event.mode} (${event.reason ?? "runtime"})` }]);
        }
        if (event.type === "review") {
          const warnings = (event.warnings || []).join("; ");
          if (warnings) {
            setMessages((m) => [...m, { role: "system", content: `Reviewer warnings: ${warnings}` }]);
          }
        }
      }
    } catch (err) {
      setMessages((m) => [...m, { role: "system", content: String(err) }]);
    } finally {
      setBusy(false);
    }
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (!settings?.ui_chat_send_on_enter) return;
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send().catch(console.error);
    }
  }

  async function submitManualSearch() {
    if (!manualQuery.trim() || !manualInput.trim()) return;
    const parsed = await api.manualSearch({ query: manualQuery, pasted_lines: manualInput });
    const lines = parsed.results.map((r) => `- ${r.title} (${r.url}) ${r.snippet}`).join("\n");
    setManualInput("");
    setManualQuery("");
    setText(`Use these manual search results to answer:\n${lines}`);
  }

  return (
    <div>
      <div className="card">
        <h3>Model Management</h3>
        <div className="row">
          <button className="secondary" onClick={() => refreshModels()}>Refresh Models</button>
          <label>Source</label>
          <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
            {[...new Set(models.map((m) => m.source_id))].map((id) => (
              <option key={id} value={id}>{models.find((x) => x.source_id === id)?.source_name}</option>
            ))}
          </select>
          <button className="secondary" onClick={testSource}>Connection Test</button>
          <label>Model</label>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {filtered.map((m) => <option key={m.model} value={m.model}>{m.model}</option>)}
          </select>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <input value={newSourceName} onChange={(e) => setNewSourceName(e.target.value)} placeholder="Source name" />
          <input value={newSourceBase} onChange={(e) => setNewSourceBase(e.target.value)} placeholder="Base URL" style={{ minWidth: 260 }} />
          <input value={newSourceAuth} onChange={(e) => setNewSourceAuth(e.target.value)} placeholder="Optional auth header/token" style={{ minWidth: 240 }} />
          <button onClick={addSource}>Add Remote Source</button>
        </div>
        {sourceStatus && <p className="small">{sourceStatus}</p>}
      </div>

      <div className="card">
        <div className="row">
          <label>
            <input type="checkbox" checked={safeMode} onChange={(e) => setSafeMode(e.target.checked)} /> Safe Mode
          </label>
        </div>
        <p className="small">Safe Mode ON disables external tools and keeps local-chat only behavior for sensitive tools.</p>
      </div>

      {pendingPermission && (
        <div className="card">
          <h3>Permission Prompt</h3>
          <p>Tool requires <span className="code">{pendingPermission}</span>.</p>
          <input value={pathScope} onChange={(e) => setPathScope(e.target.value)} style={{ minWidth: 520 }} />
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={() => grant("once")}>Allow Once</button>
            <button onClick={() => grant("session")}>Allow Session</button>
            <button className="secondary" onClick={() => grant("always")}>Allow Always</button>
            <button className="danger" onClick={() => setPendingPermission("")}>Deny</button>
          </div>
        </div>
      )}

      {manualQuery && (
        <div className="card">
          <h3>Manual Search Fallback</h3>
          <p className="small">Query: <span className="code">{manualQuery}</span></p>
          <textarea
            style={{ width: "100%", minHeight: 100 }}
            value={manualInput}
            onChange={(e) => setManualInput(e.target.value)}
            placeholder="Paste URLs or title|url|snippet lines"
          />
          <div className="row" style={{ marginTop: 8 }}>
            <button onClick={submitManualSearch}>Submit Manual Results</button>
          </div>
        </div>
      )}

      <div className="card">
        <div className={`chat-log ${settings?.ui_chat_compact_mode ? "compact" : ""}`} ref={chatLogRef}>
          {messages.map((m, i) => (
            <div key={i} className={`msg-${m.role}`}>
              {settings?.ui_chat_show_role_badges === false ? "" : `[${m.role}] `}
              {settings?.ui_chat_show_timestamps ? `${new Date().toLocaleTimeString()} ` : ""}
              {m.content}
              {settings?.ui_chat_streaming_cursor && m.role === "assistant" && i === messages.length - 1 ? "▌" : ""}
            </div>
          ))}
        </div>
        {lastRunId && settings?.ui_chat_show_run_report_link !== false && <p className="small">Run report available: {lastRunId} (see Audit {"->"} Runs)</p>}
        <div className="row" style={{ marginTop: 10 }}>
          <textarea
            rows={Math.max(2, Math.min(16, settings?.ui_chat_input_rows ?? 4))}
            style={{ flex: 1, minHeight: 80 }}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onInputKeyDown}
          />
          <button onClick={send} disabled={busy}>{busy ? "Streaming..." : "Send"}</button>
        </div>
      </div>
    </div>
  );
}
