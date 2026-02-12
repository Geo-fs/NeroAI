const { contextBridge, ipcRenderer, shell } = require("electron");

contextBridge.exposeInMainWorld("neroMeta", {
  appName: "NeroAI",
  backendBaseUrl: "http://127.0.0.1:8000"
});

contextBridge.exposeInMainWorld("neroDesktop", {
  toggleThinkBox: () => ipcRenderer.invoke("thinkbox:toggle"),
  closeThinkBox: () => ipcRenderer.invoke("thinkbox:close"),
  setThinkBoxPin: (pinned) => ipcRenderer.invoke("thinkbox:set-pin", { pinned }),
  updateThinkBoxHotkey: (hotkey, enabled) => ipcRenderer.invoke("thinkbox:update-hotkey", { hotkey, enabled }),
  getThinkBoxHotkeyStatus: () => ipcRenderer.invoke("thinkbox:get-hotkey-status"),
  captureScreen: (payload) => ipcRenderer.invoke("thinkbox:capture", payload || { source: "active_window" }),
  openExternal: (url) => shell.openExternal(url),
  onThinkBoxFocusInput: (handler) => {
    const listener = () => handler();
    ipcRenderer.on("thinkbox:focus-input", listener);
    return () => ipcRenderer.removeListener("thinkbox:focus-input", listener);
  }
});
