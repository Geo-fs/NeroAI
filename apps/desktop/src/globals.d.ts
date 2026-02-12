export {};

declare global {
  interface Window {
    neroMeta?: {
      appName: string;
      backendBaseUrl: string;
    };
    neroDesktop?: {
      toggleThinkBox: () => Promise<{ ok: boolean }>;
      closeThinkBox: () => Promise<{ ok: boolean }>;
      setThinkBoxPin: (pinned: boolean) => Promise<{ ok: boolean; pinned: boolean }>;
      updateThinkBoxHotkey: (hotkey: string, enabled: boolean) => Promise<{ ok: boolean; hotkey: string; error?: string }>;
      getThinkBoxHotkeyStatus: () => Promise<{ registered: boolean; hotkey: string; error?: string }>;
      captureScreen: (payload: { source: "active_window" | "region"; region?: { x: number; y: number; w: number; h: number } }) => Promise<{ image_data_url: string; source: string }>;
      openExternal: (url: string) => Promise<void>;
      onThinkBoxFocusInput: (handler: () => void) => () => void;
    };
  }
}
