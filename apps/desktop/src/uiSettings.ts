import { SettingsDef } from "./api";

export function applyUiSettingsToDocument(settings: SettingsDef): void {
  const root = document.documentElement;
  const body = document.body;
  root.style.setProperty("--font-scale", String((settings.ui_font_scale_percent ?? 100) / 100));
  root.style.setProperty("--spacing-scale", String((settings.ui_spacing_scale_percent ?? 100) / 100));
  root.style.setProperty("--card-radius", `${settings.ui_card_roundness ?? 12}px`);
  root.style.setProperty("--sidebar-width", `${settings.ui_sidebar_width ?? 240}px`);
  root.style.setProperty("--focus-ring-thickness", `${settings.ui_focus_ring_thickness ?? 2}px`);
  root.style.setProperty("--line-height-chat", `${(settings.ui_chat_line_height_percent ?? 145) / 100}`);

  const shadowMap: Record<string, string> = {
    none: "none",
    low: "0 2px 8px rgba(11,31,58,0.06)",
    medium: "0 6px 20px rgba(11,31,58,0.08)",
    high: "0 12px 28px rgba(11,31,58,0.14)",
  };
  root.style.setProperty("--card-shadow", shadowMap[settings.ui_card_shadow_level ?? "medium"] ?? shadowMap.medium);
  root.style.setProperty("--border-radius-sharp", settings.ui_border_style === "sharp" ? "0px" : "8px");

  body.classList.remove("theme-light", "theme-dark", "theme-system");
  body.classList.add(`theme-${settings.ui_theme_mode ?? "system"}`);
  body.classList.remove("accent-blue", "accent-teal", "accent-green", "accent-orange", "accent-red");
  body.classList.add(`accent-${settings.ui_theme_accent ?? "blue"}`);
  body.classList.remove("density-compact", "density-comfortable", "density-cozy");
  body.classList.add(`density-${settings.ui_density ?? "comfortable"}`);

  body.classList.toggle("reduce-motion", !!settings.ui_reduce_motion || !settings.ui_animations_enabled);
  body.classList.toggle("high-contrast", !!settings.ui_high_contrast);
  body.classList.toggle("sidebar-collapsed", !!settings.ui_sidebar_collapsed);
  body.classList.toggle("palette-no-blur", !settings.ui_palette_blur_background);
  body.classList.toggle("focus-ring-off", !settings.ui_focus_ring_enabled);
}
