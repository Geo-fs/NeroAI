const { app, BrowserWindow, globalShortcut, ipcMain, desktopCapturer, screen } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

const isDev = !!process.env.VITE_DEV_SERVER_URL;
const BACKEND_HEALTH_URL = process.env.NEROAI_BACKEND_HEALTH_URL || "http://127.0.0.1:8000/api/v1/health";
const BACKEND_START_TIMEOUT_MS = 60_000;
const BACKEND_POLL_INTERVAL_MS = 700;

let mainWindow = null;
let splashWindow = null;
let thinkBoxWindow = null;
let backendProcess = null;
let backendOwned = false;
let thinkboxSettings = {
  thinkbox_enabled: true,
  thinkbox_hotkey: "Control+Alt+Space",
  thinkbox_position: "bottom-right",
  thinkbox_size_percent: 20,
  thinkbox_pin_default: false,
  thinkbox_no_focus_steal: false,
};
let registeredHotkey = "";
let hotkeyError = "";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function splashHtml(message, isError = false) {
  const bg = isError ? "#2b0f0f" : "#0b1f3a";
  return `
  <html>
    <body style="margin:0;font-family:Segoe UI,Calibri,sans-serif;background:${bg};color:#fff;display:flex;align-items:center;justify-content:center;">
      <div style="text-align:center;padding:20px;">
        <h2 style="margin:0 0 8px 0;">NeroAI</h2>
        <div style="opacity:0.95;">${message}</div>
      </div>
    </body>
  </html>`;
}

function setSplashMessage(message, isError = false) {
  if (!splashWindow || splashWindow.isDestroyed()) return;
  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHtml(message, isError))}`);
}

async function isBackendHealthy() {
  try {
    const response = await fetch(BACKEND_HEALTH_URL, { method: "GET" });
    return response.ok;
  } catch (_err) {
    return false;
  }
}

function getBackendPythonCandidates(backendDir) {
  const venvPython = path.join(backendDir, ".venv", "Scripts", "python.exe");
  const explicit = process.env.NEROAI_BACKEND_PYTHON;
  const candidates = [];
  if (explicit) candidates.push(explicit);
  if (fs.existsSync(venvPython)) candidates.push(venvPython);
  candidates.push("python");
  candidates.push("py");
  return candidates;
}

function resolveBackendDir() {
  const explicit = process.env.NEROAI_BACKEND_DIR;
  const candidates = [
    explicit,
    path.join(process.resourcesPath || "", "backend"),
    path.resolve(__dirname, "../../backend"),
    path.resolve(process.cwd(), "apps/backend"),
    path.resolve(process.cwd(), "backend"),
  ].filter(Boolean);

  for (const item of candidates) {
    const appMain = path.join(item, "app", "main.py");
    if (fs.existsSync(appMain)) {
      return item;
    }
  }
  return null;
}

function startBackendProcess() {
  const backendDir = resolveBackendDir();
  if (!backendDir) return false;

  const candidates = getBackendPythonCandidates(backendDir);
  for (const cmd of candidates) {
    const args = cmd.toLowerCase().endsWith("py")
      ? ["-3", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
      : ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"];
    try {
      backendProcess = spawn(cmd, args, {
        cwd: backendDir,
        stdio: "ignore",
        windowsHide: true,
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
      });
      backendOwned = true;
      backendProcess.on("exit", () => {
        backendProcess = null;
      });
      return true;
    } catch (_err) {
      backendProcess = null;
      backendOwned = false;
    }
  }
  return false;
}

async function ensureBackendReady() {
  if (await isBackendHealthy()) {
    return true;
  }
  setSplashMessage("Starting backend service...");
  startBackendProcess();
  const deadline = Date.now() + BACKEND_START_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if (await isBackendHealthy()) {
      return true;
    }
    setSplashMessage("Waiting for backend to become ready...");
    await sleep(BACKEND_POLL_INTERVAL_MS);
  }
  return false;
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 300,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    movable: false,
    show: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  setSplashMessage("Starting backend service...");
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    show: false,
    backgroundColor: "#f4f6fb",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  mainWindow.webContents.on("did-fail-load", (_event, code, desc, url) => {
    const html = `
    <html><body style="font-family:Segoe UI,Calibri,sans-serif;padding:24px;background:#fff;">
      <h2>NeroAI UI failed to load</h2>
      <p><b>URL:</b> ${url || "n/a"}</p>
      <p><b>Error:</b> ${code} ${desc}</p>
      <p>Check desktop build output and backend availability.</p>
    </body></html>`;
    mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`).catch(() => {});
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  mainWindow.webContents.on("render-process-gone", (_event, details) => {
    const html = `
    <html><body style="font-family:Segoe UI,Calibri,sans-serif;padding:24px;background:#fff;">
      <h2>NeroAI renderer crashed</h2>
      <p><b>Reason:</b> ${details.reason}</p>
      <p>Restart the app. If this persists, run in dev mode to inspect logs.</p>
    </body></html>`;
    mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`).catch(() => {});
    mainWindow.show();
  });

  mainWindow.webContents.once("did-finish-load", () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  if (isDev) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL).catch(() => {});
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html")).catch(() => {});
  }
}

function normalizeAccelerator(accel) {
  if (!accel || typeof accel !== "string") return "CommandOrControl+Alt+Space";
  return accel
    .replaceAll("Ctrl", "CommandOrControl")
    .replaceAll("Control", "CommandOrControl")
    .trim();
}

function getThinkBoxDimensions(sizePercent) {
  const display = screen.getPrimaryDisplay();
  const area = display.workArea;
  const percent = Math.max(15, Math.min(45, Number(sizePercent || 20)));
  const width = Math.max(320, Math.round(area.width * (percent / 100)));
  const height = Math.max(280, Math.round(area.height * (percent / 100)));
  return { area, width, height };
}

function getThinkBoxPosition(position, width, height) {
  const display = screen.getPrimaryDisplay();
  const area = display.workArea;
  if (position === "near-cursor") {
    const cursor = screen.getCursorScreenPoint();
    const x = Math.max(area.x, Math.min(cursor.x + 16, area.x + area.width - width));
    const y = Math.max(area.y, Math.min(cursor.y + 16, area.y + area.height - height));
    return { x, y };
  }
  return {
    x: Math.max(area.x, area.x + area.width - width - 16),
    y: Math.max(area.y, area.y + area.height - height - 16),
  };
}

function getThinkBoxUrl() {
  if (isDev) {
    return `${process.env.VITE_DEV_SERVER_URL}?thinkbox=1`;
  }
  const fileUrl = pathToFileURL(path.join(__dirname, "../dist/index.html")).toString();
  return `${fileUrl}?thinkbox=1`;
}

function createThinkBoxWindow() {
  if (thinkBoxWindow && !thinkBoxWindow.isDestroyed()) {
    return thinkBoxWindow;
  }
  const { width, height } = getThinkBoxDimensions(thinkboxSettings.thinkbox_size_percent);
  const pos = getThinkBoxPosition(thinkboxSettings.thinkbox_position, width, height);
  thinkBoxWindow = new BrowserWindow({
    width,
    height,
    x: pos.x,
    y: pos.y,
    frame: false,
    transparent: false,
    resizable: true,
    minimizable: false,
    maximizable: false,
    skipTaskbar: true,
    show: false,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  thinkBoxWindow.setMenuBarVisibility(false);
  thinkBoxWindow.webContents.on("before-input-event", (event, input) => {
    if (input.type === "keyDown" && input.key === "Escape") {
      event.preventDefault();
      thinkBoxWindow.hide();
    }
  });
  thinkBoxWindow.on("closed", () => {
    thinkBoxWindow = null;
  });
  thinkBoxWindow.webContents.on("did-finish-load", () => {
    thinkBoxWindow?.webContents.send("thinkbox:focus-input");
  });
  thinkBoxWindow.loadURL(getThinkBoxUrl()).catch(() => {});
  return thinkBoxWindow;
}

async function refreshThinkboxSettings() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/v1/settings", { method: "GET" });
    if (!res.ok) return thinkboxSettings;
    const json = await res.json();
    thinkboxSettings = { ...thinkboxSettings, ...json };
  } catch (_err) {
    // Keep defaults when backend is unavailable.
  }
  return thinkboxSettings;
}

function showThinkBox() {
  if (!thinkboxSettings.thinkbox_enabled) return;
  const win = createThinkBoxWindow();
  const { width, height } = getThinkBoxDimensions(thinkboxSettings.thinkbox_size_percent);
  const pos = getThinkBoxPosition(thinkboxSettings.thinkbox_position, width, height);
  win.setBounds({ x: pos.x, y: pos.y, width, height });
  win.setAlwaysOnTop(true, "floating");
  if (thinkboxSettings.thinkbox_no_focus_steal) {
    win.showInactive();
  } else {
    win.show();
    win.focus();
  }
}

function toggleThinkBox() {
  const win = createThinkBoxWindow();
  if (win.isVisible()) {
    win.hide();
    return;
  }
  showThinkBox();
}

function registerThinkBoxHotkey() {
  if (registeredHotkey) {
    globalShortcut.unregister(registeredHotkey);
    registeredHotkey = "";
  }
  hotkeyError = "";
  if (!thinkboxSettings.thinkbox_enabled) {
    return false;
  }
  const accelerator = normalizeAccelerator(thinkboxSettings.thinkbox_hotkey);
  const ok = globalShortcut.register(accelerator, () => {
    toggleThinkBox();
  });
  if (!ok) {
    hotkeyError = `Unable to register hotkey: ${accelerator}`;
    return false;
  }
  registeredHotkey = accelerator;
  return true;
}

async function captureActiveWindowDataUrl() {
  const { width, height } = getThinkBoxDimensions(30);
  const sources = await desktopCapturer.getSources({
    types: ["window", "screen"],
    thumbnailSize: { width, height },
    fetchWindowIcons: false,
  });
  if (!sources.length) {
    throw new Error("No capture sources available.");
  }
  const source = sources.find((item) => item.id.startsWith("window:")) || sources[0];
  const dataUrl = source.thumbnail.toDataURL();
  if (!dataUrl) {
    throw new Error("Capture failed.");
  }
  return dataUrl;
}

function cropDataUrl(dataUrl, region) {
  if (!region) return dataUrl;
  return dataUrl;
}

function wireIpc() {
  ipcMain.handle("thinkbox:toggle", () => {
    toggleThinkBox();
    return { ok: true };
  });
  ipcMain.handle("thinkbox:close", () => {
    if (thinkBoxWindow && !thinkBoxWindow.isDestroyed()) {
      thinkBoxWindow.hide();
    }
    return { ok: true };
  });
  ipcMain.handle("thinkbox:set-pin", (_event, payload) => {
    const pinned = !!(payload && payload.pinned);
    if (thinkBoxWindow && !thinkBoxWindow.isDestroyed()) {
      thinkBoxWindow.setAlwaysOnTop(pinned, "floating");
    }
    return { ok: true, pinned };
  });
  ipcMain.handle("thinkbox:update-hotkey", async (_event, payload) => {
    if (payload && typeof payload.hotkey === "string") {
      thinkboxSettings.thinkbox_hotkey = payload.hotkey;
    }
    if (payload && typeof payload.enabled === "boolean") {
      thinkboxSettings.thinkbox_enabled = payload.enabled;
    }
    const registered = registerThinkBoxHotkey();
    return { ok: registered, error: hotkeyError, hotkey: registeredHotkey || normalizeAccelerator(thinkboxSettings.thinkbox_hotkey) };
  });
  ipcMain.handle("thinkbox:get-hotkey-status", () => {
    return { registered: !!registeredHotkey, hotkey: registeredHotkey || normalizeAccelerator(thinkboxSettings.thinkbox_hotkey), error: hotkeyError };
  });
  ipcMain.handle("thinkbox:capture", async (_event, payload) => {
    const source = payload?.source || "active_window";
    if (source !== "active_window" && source !== "region") {
      throw new Error("Unsupported capture source.");
    }
    const dataUrl = await captureActiveWindowDataUrl();
    return { image_data_url: cropDataUrl(dataUrl, payload?.region || null), source };
  });
}

app.whenReady().then(() => {
  wireIpc();
  createSplashWindow();
  ensureBackendReady().then((ok) => {
    if (!ok) {
      setSplashMessage("Backend failed to start. Check Python/.venv and backend dependencies.", true);
      return;
    }
    refreshThinkboxSettings().finally(() => {
      registerThinkBoxHotkey();
    });
    createWindow();
  });
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("before-quit", () => {
  if (backendOwned && backendProcess) {
    try {
      backendProcess.kill();
    } catch (_err) {
      // No-op: app is quitting anyway.
    }
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});
