import { KeyboardEvent as ReactKeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, SettingsDef } from "./api";

type ModeId = "screen_help" | "explain" | "steps" | "extract" | "research";
type PermissionPrompt = {
  permission: "screen.capture" | "web.search" | "clipboard.read" | "clipboard.write" | "filesystem.read";
  action: "capture" | "send" | "clipboard_read" | "clipboard_write";
};

const modeItems: { id: ModeId; label: string }[] = [
  { id: "screen_help", label: "Screen Help" },
  { id: "explain", label: "Explain" },
  { id: "steps", label: "Steps" },
  { id: "extract", label: "Extract" },
  { id: "research", label: "Research" },
];

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
  max_bytes_read_per_run: 5000000,
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
  thinkbox_show_connection_dot: true,
  thinkbox_show_safe_mode_badge: true,
  thinkbox_show_mode_chips: true,
  thinkbox_default_mode: "screen_help",
  thinkbox_expand_by_default: false,
  thinkbox_enable_ctrl_l_focus: true,
  thinkbox_enable_enter_to_send: true,
  thinkbox_show_capture_thumbnail: true,
  thinkbox_capture_on_open: false,
  thinkbox_capture_on_mode_change: false,
  thinkbox_awareness_show_countdown: true,
  thinkbox_awareness_require_pin: true,
  thinkbox_quick_action_copy: true,
  thinkbox_quick_action_steps: true,
  thinkbox_quick_action_research: true,
  thinkbox_quick_action_clipboard: true,
  thinkbox_remember_last_text: false,
  thinkbox_clear_text_on_send: false,
  thinkbox_status_toast_seconds: 3,
  thinkbox_opacity_percent: 98,
  thinkbox_corner_roundness: 10,
  thinkbox_border_width: 1,
  thinkbox_border_color: "#d7e2f0",
  thinkbox_thumbnail_height: 120,
};

const LAST_TEXT_KEY = "nero_thinkbox_last_text";

export function ThinkBoxApp() {
  const [settings, setSettings] = useState<SettingsDef>(defaults);
  const [connected, setConnected] = useState(false);
  const [mode, setMode] = useState<ModeId>("screen_help");
  const [text, setText] = useState("");
  const [response, setResponse] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [captureSource, setCaptureSource] = useState<"active_window" | "region">("active_window");
  const [captureId, setCaptureId] = useState("");
  const [freezeCapture, setFreezeCapture] = useState(false);
  const [thumbUrl, setThumbUrl] = useState("");
  const [pin, setPin] = useState(false);
  const [toggleClipboard, setToggleClipboard] = useState(false);
  const [toggleFiles, setToggleFiles] = useState(false);
  const [toggleMultiAgent, setToggleMultiAgent] = useState(false);
  const [awareness, setAwareness] = useState(false);
  const [awarenessRemaining, setAwarenessRemaining] = useState(0);
  const [permissionPrompt, setPermissionPrompt] = useState<PermissionPrompt | null>(null);
  const [status, setStatus] = useState("");
  const [selectedText, setSelectedText] = useState("");
  const [clipboardText, setClipboardText] = useState("");
  const [region, setRegion] = useState({ x: 0, y: 0, w: 640, h: 420 });
  const [lastActivityAt, setLastActivityAt] = useState(Date.now());
  const inputRef = useRef<HTMLInputElement | null>(null);

  const conciseResponse = useMemo(() => {
    if (expanded) return response;
    const lines = response.split("\n");
    return lines.slice(0, Math.max(3, Math.min(8, settings.thinkbox_response_bullet_max ?? 8))).join("\n");
  }, [expanded, response, settings.thinkbox_response_bullet_max]);

  const shellStyle = useMemo(
    () => ({
      opacity: Math.max(0.5, Math.min(1, (settings.thinkbox_opacity_percent ?? 98) / 100)),
      borderRadius: `${settings.thinkbox_corner_roundness ?? 10}px`,
      border: `${settings.thinkbox_border_width ?? 1}px solid ${settings.thinkbox_border_color ?? "#d7e2f0"}`,
      backdropFilter: settings.thinkbox_background_blur ? "blur(8px)" : "none",
    }),
    [
      settings.thinkbox_opacity_percent,
      settings.thinkbox_corner_roundness,
      settings.thinkbox_border_width,
      settings.thinkbox_border_color,
      settings.thinkbox_background_blur,
    ],
  );

  async function boot() {
    try {
      const cfg = await api.getSettings();
      setSettings(cfg);
      setMode((cfg.thinkbox_default_mode as ModeId) ?? "screen_help");
      setCaptureSource(cfg.thinkbox_capture_default ?? "active_window");
      setPin(cfg.thinkbox_pin_default ?? false);
      setAwareness(cfg.thinkbox_awareness_default ?? false);
      setAwarenessRemaining((cfg.thinkbox_awareness_minutes ?? 10) * 60);
      setExpanded(cfg.thinkbox_expand_by_default ?? false);
      if (cfg.thinkbox_remember_last_text) {
        setText(localStorage.getItem(LAST_TEXT_KEY) ?? "");
      }
      setConnected(true);
      if (window.neroDesktop) {
        await window.neroDesktop.setThinkBoxPin(cfg.thinkbox_pin_default ?? false);
      }
      if (cfg.thinkbox_capture_on_open) {
        await requestCapture();
      }
    } catch (err) {
      setStatus(String(err));
    }
  }

  useEffect(() => {
    boot().catch((err) => setStatus(String(err)));
    const off = window.neroDesktop?.onThinkBoxFocusInput(() => {
      inputRef.current?.focus();
    });
    const onMove = () => setLastActivityAt(Date.now());
    const onKey = (event: globalThis.KeyboardEvent) => {
      setLastActivityAt(Date.now());
      if (event.key === "Escape") {
        window.neroDesktop?.closeThinkBox().catch(() => undefined);
      }
      if ((settings.thinkbox_enable_ctrl_l_focus ?? true) && event.ctrlKey && event.key.toLowerCase() === "l") {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousemove", onMove);
    return () => {
      off?.();
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousemove", onMove);
    };
  }, [settings.thinkbox_enable_ctrl_l_focus]);

  useEffect(() => {
    if (!status) return;
    const seconds = Math.max(1, settings.thinkbox_status_toast_seconds ?? 3);
    const timer = window.setTimeout(() => setStatus(""), seconds * 1000);
    return () => window.clearTimeout(timer);
  }, [status, settings.thinkbox_status_toast_seconds]);

  useEffect(() => {
    if (pin || (settings.thinkbox_auto_hide_seconds ?? 30) <= 0) return;
    const interval = window.setInterval(() => {
      const idle = Math.floor((Date.now() - lastActivityAt) / 1000);
      if (idle >= (settings.thinkbox_auto_hide_seconds ?? 30) && !busy) {
        window.neroDesktop?.closeThinkBox().catch(() => undefined);
      }
    }, 1000);
    return () => window.clearInterval(interval);
  }, [pin, settings.thinkbox_auto_hide_seconds, lastActivityAt, busy]);

  useEffect(() => {
    if (!awareness) return;
    if ((settings.thinkbox_awareness_require_pin ?? true) && !pin) {
      setAwareness(false);
      return;
    }
    if (awarenessRemaining <= 0) {
      setAwareness(false);
      return;
    }
    const tick = window.setInterval(() => {
      setAwarenessRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => window.clearInterval(tick);
  }, [awareness, awarenessRemaining, pin, settings.thinkbox_awareness_require_pin]);

  useEffect(() => {
    if (!awareness || (settings.thinkbox_awareness_interval_seconds ?? 0) <= 0) return;
    const interval = window.setInterval(() => {
      requestCapture().catch(() => undefined);
    }, (settings.thinkbox_awareness_interval_seconds ?? 0) * 1000);
    return () => window.clearInterval(interval);
  }, [awareness, settings.thinkbox_awareness_interval_seconds, captureSource, region.x, region.y, region.w, region.h]);

  useEffect(() => {
    if (!(settings.thinkbox_capture_on_mode_change ?? false)) return;
    requestCapture().catch(() => undefined);
  }, [mode, settings.thinkbox_capture_on_mode_change]);

  async function ensurePermission(prompt: PermissionPrompt, path?: string) {
    const check = await api.checkPermission(prompt.permission, path);
    if (check.granted) return true;
    setPermissionPrompt(prompt);
    return false;
  }

  async function grantPermission(scope: "once" | "session" | "always" | "no") {
    if (!permissionPrompt) return;
    if (scope === "no") {
      setStatus(`Denied ${permissionPrompt.permission}`);
      setPermissionPrompt(null);
      return;
    }
    await api.grantPermission({ permission: permissionPrompt.permission, scope });
    const action = permissionPrompt.action;
    setPermissionPrompt(null);
    if (action === "capture") await requestCapture();
    if (action === "send") await send();
    if (action === "clipboard_read") await readClipboard();
    if (action === "clipboard_write") await copyAnswer();
  }

  async function requestCapture() {
    if (!(await ensurePermission({ permission: "screen.capture", action: "capture" }))) return;
    try {
      const local = await window.neroDesktop?.captureScreen({
        source: captureSource,
        region: captureSource === "region" ? region : undefined,
      });
      const saved = await api.screenCapture({
        source: captureSource,
        region: captureSource === "region" ? region : undefined,
        image_data_url: local?.image_data_url,
      });
      if (!freezeCapture || !captureId) {
        setCaptureId(saved.capture_id);
      }
      setThumbUrl(saved.thumbnail_data_url ?? "");
      setStatus(`Captured ${captureSource.replace("_", " ")}.`);
    } catch (err) {
      setStatus(String(err));
    }
  }

  async function readClipboard() {
    if (!(await ensurePermission({ permission: "clipboard.read", action: "clipboard_read" }))) return;
    const out = await api.clipboardRead();
    setClipboardText(out.text || "");
  }

  async function copyAnswer() {
    if (!response.trim()) return;
    if (!(await ensurePermission({ permission: "clipboard.write", action: "clipboard_write" }))) return;
    await api.clipboardWrite(response);
    setStatus("Answer copied.");
  }

  async function send() {
    if (!text.trim()) return;
    if (mode === "research" && !(await ensurePermission({ permission: "web.search", action: "send" }))) return;
    if (toggleFiles && !(await ensurePermission({ permission: "filesystem.read", action: "send" }))) return;
    setBusy(true);
    setLastActivityAt(Date.now());
    setResponse("");
    setStatus("");
    try {
      const reply = await api.thinkboxMessage({
        text,
        mode,
        toggles: {
          safe_mode: settings.safe_mode_default,
          clipboard: toggleClipboard,
          files: toggleFiles,
          multi_agent: toggleMultiAgent,
          awareness,
        },
        context: {
          frozen_capture_id: freezeCapture ? captureId : undefined,
          selected_text: selectedText,
          clipboard_text: toggleClipboard ? clipboardText : undefined,
        },
      });
      for await (const event of api.thinkboxStream(reply.run_id)) {
        if (event.type === "token") {
          setResponse((prev) => prev + String(event.content || ""));
        }
        if (event.type === "fallback_mode") {
          setStatus(`Fallback mode active: ${String(event.mode || "search_answer")}`);
        }
        if (event.type === "error") {
          setStatus(String(event.detail || "Think Box request failed."));
        }
      }
      if (settings.thinkbox_clear_text_on_send) {
        setText("");
      }
      if (settings.thinkbox_remember_last_text) {
        localStorage.setItem(LAST_TEXT_KEY, text);
      }
    } catch (err) {
      setStatus(String(err));
    } finally {
      setBusy(false);
    }
  }

  function toggleAwareness() {
    if (!awareness) {
      setAwarenessRemaining((settings.thinkbox_awareness_minutes ?? 10) * 60);
    }
    setAwareness((prev) => !prev);
    setLastActivityAt(Date.now());
  }

  function onInputKeyDown(event: ReactKeyboardEvent<HTMLInputElement>) {
    if ((settings.thinkbox_enable_enter_to_send ?? true) && event.key === "Enter") {
      event.preventDefault();
      send().catch(console.error);
    }
  }

  return (
    <div className="thinkbox-shell" style={shellStyle}>
      <div className="thinkbox-top">
        <div className="row">
          <strong>Think Box</strong>
          {settings.thinkbox_show_connection_dot !== false && <span className={`dot ${connected ? "ok" : "bad"}`} />}
          {settings.thinkbox_show_safe_mode_badge !== false && <span className="badge">Safe: {settings.safe_mode_default ? "ON" : "OFF"}</span>}
          {awareness && settings.thinkbox_awareness_show_countdown !== false && <span className="badge">Screen: ON ({awarenessRemaining}s)</span>}
        </div>
        <div className="row">
          <button className="secondary" onClick={() => window.neroDesktop?.setThinkBoxPin(!pin).then(() => setPin((v) => !v)).catch(() => undefined)}>
            {pin ? "Unpin" : "Pin"}
          </button>
          <button className="danger" onClick={() => window.neroDesktop?.closeThinkBox().catch(() => undefined)}>Close</button>
        </div>
      </div>

      <div className="thinkbox-card">
        <div className="row">
          <label>Capture</label>
          <select value={captureSource} onChange={(e) => setCaptureSource(e.target.value as "active_window" | "region")}>
            <option value="active_window">Active window</option>
            <option value="region">Region</option>
          </select>
          <button onClick={() => requestCapture().catch((err) => setStatus(String(err)))}>Capture now</button>
          <button className="secondary" onClick={() => setCaptureSource("region")}>Pick region</button>
          <label><input type="checkbox" checked={freezeCapture} onChange={(e) => setFreezeCapture(e.target.checked)} /> Freeze</label>
        </div>
        {captureSource === "region" && (
          <div className="row">
            <input type="number" value={region.x} onChange={(e) => setRegion((r) => ({ ...r, x: parseInt(e.target.value, 10) || 0 }))} placeholder="x" />
            <input type="number" value={region.y} onChange={(e) => setRegion((r) => ({ ...r, y: parseInt(e.target.value, 10) || 0 }))} placeholder="y" />
            <input type="number" value={region.w} onChange={(e) => setRegion((r) => ({ ...r, w: parseInt(e.target.value, 10) || 0 }))} placeholder="w" />
            <input type="number" value={region.h} onChange={(e) => setRegion((r) => ({ ...r, h: parseInt(e.target.value, 10) || 0 }))} placeholder="h" />
          </div>
        )}
        <div className="small">Capture ID: {captureId || "none"}</div>
        {thumbUrl && settings.thinkbox_show_capture_thumbnail !== false && (
          <img className="thumb" style={{ maxHeight: `${settings.thinkbox_thumbnail_height ?? 120}px` }} src={thumbUrl} alt="Capture thumbnail" />
        )}
      </div>

      {permissionPrompt && (
        <div className="thinkbox-card">
          <div className="small">Permission required: <span className="code">{permissionPrompt.permission}</span></div>
          <div className="row">
            <button onClick={() => grantPermission("once")}>Once</button>
            <button onClick={() => grantPermission("session")}>Session</button>
            <button className="secondary" onClick={() => grantPermission("always")}>Always</button>
            <button className="danger" onClick={() => grantPermission("no")}>No</button>
          </div>
        </div>
      )}

      <div className="thinkbox-card">
        <input
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onInputKeyDown}
          placeholder="Ask about what is on your screen..."
        />
        <div className="row" style={{ marginTop: 6 }}>
          <button onClick={() => send().catch((err) => setStatus(String(err)))} disabled={busy}>{busy ? "Thinking..." : "Send"}</button>
          {settings.thinkbox_quick_action_clipboard !== false && (
            <button className="secondary" onClick={() => readClipboard().catch((err) => setStatus(String(err)))}>Read Clipboard</button>
          )}
          <input value={selectedText} onChange={(e) => setSelectedText(e.target.value)} placeholder="Selected text (optional)" />
        </div>
      </div>

      <div className="thinkbox-card">
        <pre className={`thinkbox-output ${expanded ? "expanded" : ""}`}>{conciseResponse || "Response will appear here."}</pre>
        <div className="row">
          <button className="secondary" onClick={() => setExpanded((v) => !v)}>{expanded ? "Less" : "More"}</button>
          {settings.thinkbox_quick_action_steps !== false && <button className="secondary" onClick={() => setMode("steps")}>Turn into steps</button>}
          {settings.thinkbox_quick_action_research !== false && <button className="secondary" onClick={() => setMode("research")}>Search web</button>}
          {settings.thinkbox_quick_action_copy !== false && <button onClick={() => copyAnswer().catch((err) => setStatus(String(err)))}>Copy answer</button>}
        </div>
      </div>

      {settings.thinkbox_show_mode_chips !== false && (
        <div className="thinkbox-modes">
          {modeItems.map((item) => (
            <button key={item.id} className={`chip ${mode === item.id ? "active" : ""}`} onClick={() => setMode(item.id)}>
              {item.label}
            </button>
          ))}
          <label className="chip-toggle"><input type="checkbox" checked={toggleClipboard} onChange={(e) => setToggleClipboard(e.target.checked)} /> Clipboard</label>
          <label className="chip-toggle"><input type="checkbox" checked={toggleFiles} onChange={(e) => setToggleFiles(e.target.checked)} /> Files</label>
          <label className="chip-toggle"><input type="checkbox" checked={toggleMultiAgent} onChange={(e) => setToggleMultiAgent(e.target.checked)} /> Multi-agent</label>
          <label className="chip-toggle"><input type="checkbox" checked={awareness} onChange={toggleAwareness} /> On-Screen Awareness</label>
        </div>
      )}

      {status && <div className="small">{status}</div>}
    </div>
  );
}
