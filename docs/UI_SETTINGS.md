# UI/UX Settings Reference

This table is generated from the backend settings registry and lists all current UI/UX settings for the main app and Think Box.

| Key | Group | Type | Default | Allowed Options / Range | Description | Scope | Danger | Restart Required |
|---|---|---|---|---|---|---|---|---|
| `thinkbox_enabled` | Think Box | bool | `True` | true / false | Enable Think Box overlay window. | profile | normal | false |
| `thinkbox_hotkey` | Think Box | string | `Control+Alt+Space` | string | Global hotkey to toggle Think Box. | profile | normal | false |
| `thinkbox_position` | Think Box | enum | `bottom-right` | bottom-right, near-cursor, custom | Think box position. | profile | normal | false |
| `thinkbox_size_percent` | Think Box | int | `20` | integer (use safe/applicable range) | Think box size percent. | profile | normal | false |
| `thinkbox_auto_hide_seconds` | Think Box | int | `30` | integer (use safe/applicable range) | Think box auto hide seconds. | profile | normal | false |
| `thinkbox_pin_default` | Think Box | bool | `False` | true / false | Think box pin default. | profile | normal | false |
| `thinkbox_no_focus_steal` | Think Box | bool | `False` | true / false | Think box no focus steal. | profile | normal | false |
| `thinkbox_capture_default` | Think Box | enum | `active_window` | active_window, region | Think box capture default. | profile | normal | false |
| `thinkbox_awareness_default` | Think Box | bool | `False` | true / false | Think box awareness default. | profile | normal | false |
| `thinkbox_awareness_minutes` | Think Box | int | `10` | integer (use safe/applicable range) | Think box awareness minutes. | profile | normal | false |
| `thinkbox_awareness_interval_seconds` | Think Box | int | `0` | integer (use safe/applicable range) | Think box awareness interval seconds. | profile | normal | false |
| `thinkbox_store_screenshots` | Think Box | bool | `False` | true / false | Think box store screenshots. | profile | normal | false |
| `thinkbox_store_thumbnail` | Think Box | bool | `False` | true / false | Think box store thumbnail. | profile | normal | false |
| `ui_density` | Main App UI | enum | `comfortable` | compact, comfortable, cozy | Overall control density for main app surfaces. | profile | normal | false |
| `ui_font_scale_percent` | Accessibility | int | `100` | integer (use safe/applicable range) | Font scale percent. | profile | normal | false |
| `ui_sidebar_collapsed` | Main App UI | bool | `False` | true / false | Sidebar collapsed. | profile | normal | false |
| `ui_sidebar_width` | Main App UI | int | `240` | integer (use safe/applicable range) | Sidebar width. | profile | normal | false |
| `ui_show_topbar` | Main App UI | bool | `True` | true / false | Show topbar. | profile | normal | false |
| `ui_topbar_compact` | Main App UI | bool | `False` | true / false | Topbar compact. | profile | normal | false |
| `ui_show_command_palette_hint` | Main App UI | bool | `True` | true / false | Show command palette hint. | profile | normal | false |
| `ui_animations_enabled` | Main App UI | bool | `True` | true / false | Animations enabled. | profile | normal | false |
| `ui_animation_speed` | Main App UI | enum | `normal` | slow, normal, fast | Animation speed. | profile | normal | false |
| `ui_reduce_motion` | Accessibility | bool | `False` | true / false | Reduce motion. | profile | normal | false |
| `ui_high_contrast` | Accessibility | bool | `False` | true / false | High contrast. | profile | normal | false |
| `ui_theme_mode` | Main App UI | enum | `system` | system, light, dark | Theme mode. | profile | normal | false |
| `ui_theme_accent` | Main App UI | enum | `blue` | blue, teal, green, orange, red | Theme accent. | profile | normal | false |
| `ui_card_roundness` | Main App UI | int | `12` | integer (use safe/applicable range) | Card roundness. | profile | normal | false |
| `ui_card_shadow_level` | Main App UI | enum | `medium` | none, low, medium, high | Card shadow level. | profile | normal | false |
| `ui_border_style` | Main App UI | enum | `soft` | soft, sharp | Border style. | profile | normal | false |
| `ui_focus_ring_enabled` | Accessibility | bool | `True` | true / false | Focus ring enabled. | profile | normal | false |
| `ui_focus_ring_thickness` | Accessibility | int | `2` | integer (use safe/applicable range) | Focus ring thickness. | profile | normal | false |
| `ui_spacing_scale_percent` | Main App UI | int | `100` | integer (use safe/applicable range) | Spacing scale percent. | profile | normal | false |
| `ui_chat_line_height_percent` | Main App UI | int | `145` | integer (use safe/applicable range) | Chat line height percent. | profile | normal | false |
| `ui_chat_show_timestamps` | Main App UI | bool | `False` | true / false | Chat show timestamps. | profile | normal | false |
| `ui_chat_show_role_badges` | Main App UI | bool | `True` | true / false | Chat show role badges. | profile | normal | false |
| `ui_chat_streaming_cursor` | Main App UI | bool | `True` | true / false | Chat streaming cursor. | profile | normal | false |
| `ui_chat_autoscroll` | Main App UI | bool | `True` | true / false | Chat autoscroll. | profile | normal | false |
| `ui_chat_compact_mode` | Main App UI | bool | `False` | true / false | Chat compact mode. | profile | normal | false |
| `ui_chat_input_rows` | Main App UI | int | `4` | integer (use safe/applicable range) | Chat input rows. | profile | normal | false |
| `ui_chat_send_on_enter` | Main App UI | bool | `False` | true / false | Chat send on enter. | profile | normal | false |
| `ui_chat_show_run_report_link` | Main App UI | bool | `True` | true / false | Chat show run report link. | profile | normal | false |
| `ui_audit_rows_per_page` | Main App UI | int | `50` | integer (use safe/applicable range) | Audit rows per page. | profile | normal | false |
| `ui_workflow_editor_font_size` | Main App UI | int | `13` | integer (use safe/applicable range) | Workflow editor font size. | profile | normal | false |
| `ui_settings_show_descriptions` | Main App UI | bool | `True` | true / false | Settings show descriptions. | profile | normal | false |
| `ui_settings_show_advanced_badges` | Main App UI | bool | `True` | true / false | Settings show advanced badges. | profile | normal | false |
| `ui_settings_remember_last_category` | Main App UI | bool | `True` | true / false | Settings remember last category. | profile | normal | false |
| `ui_palette_max_results` | Main App UI | int | `12` | integer (use safe/applicable range) | Palette max results. | profile | normal | false |
| `ui_palette_blur_background` | Main App UI | bool | `True` | true / false | Palette blur background. | profile | normal | false |
| `thinkbox_opacity_percent` | Think Box | int | `98` | integer (use safe/applicable range) | Think box opacity percent. | profile | normal | false |
| `thinkbox_corner_roundness` | Think Box | int | `10` | integer (use safe/applicable range) | Think box corner roundness. | profile | normal | false |
| `thinkbox_border_width` | Think Box | int | `1` | integer (use safe/applicable range) | Think box border width. | profile | normal | false |
| `thinkbox_border_color` | Think Box | string | `#d7e2f0` | string | Think box border color. | profile | normal | false |
| `thinkbox_background_blur` | Think Box | bool | `False` | true / false | Think box background blur. | profile | normal | false |
| `thinkbox_show_connection_dot` | Think Box | bool | `True` | true / false | Think box show connection dot. | profile | normal | false |
| `thinkbox_show_safe_mode_badge` | Think Box | bool | `True` | true / false | Think box show safe mode badge. | profile | normal | false |
| `thinkbox_show_mode_chips` | Think Box | bool | `True` | true / false | Think box show mode chips. | profile | normal | false |
| `thinkbox_default_mode` | Think Box | enum | `screen_help` | screen_help, explain, steps, extract, research | Think box default mode. | profile | normal | false |
| `thinkbox_response_bullet_min` | Think Box | int | `3` | integer (use safe/applicable range) | Think box response bullet min. | profile | normal | false |
| `thinkbox_response_bullet_max` | Think Box | int | `8` | integer (use safe/applicable range) | Think box response bullet max. | profile | normal | false |
| `thinkbox_expand_by_default` | Think Box | bool | `False` | true / false | Think box expand by default. | profile | normal | false |
| `thinkbox_enable_ctrl_l_focus` | Think Box | bool | `True` | true / false | Think box enable ctrl l focus. | profile | normal | false |
| `thinkbox_enable_enter_to_send` | Think Box | bool | `True` | true / false | Think box enable enter to send. | profile | normal | false |
| `thinkbox_show_capture_thumbnail` | Think Box | bool | `True` | true / false | Think box show capture thumbnail. | profile | normal | false |
| `thinkbox_thumbnail_height` | Think Box | int | `120` | integer (use safe/applicable range) | Think box thumbnail height. | profile | normal | false |
| `thinkbox_region_selector_grid` | Think Box | bool | `True` | true / false | Think box region selector grid. | profile | normal | false |
| `thinkbox_capture_quality` | Think Box | enum | `medium` | low, medium, high | Think box capture quality. | profile | normal | false |
| `thinkbox_capture_on_open` | Think Box | bool | `False` | true / false | Think box capture on open. | profile | normal | false |
| `thinkbox_capture_on_mode_change` | Think Box | bool | `False` | true / false | Think box capture on mode change. | profile | normal | false |
| `thinkbox_awareness_show_countdown` | Think Box | bool | `True` | true / false | Think box awareness show countdown. | profile | normal | false |
| `thinkbox_awareness_require_pin` | Think Box | bool | `True` | true / false | Think box awareness require pin. | profile | normal | false |
| `thinkbox_awareness_pause_when_unfocused` | Think Box | bool | `True` | true / false | Think box awareness pause when unfocused. | profile | normal | false |
| `thinkbox_quick_action_copy` | Think Box | bool | `True` | true / false | Think box quick action copy. | profile | normal | false |
| `thinkbox_quick_action_steps` | Think Box | bool | `True` | true / false | Think box quick action steps. | profile | normal | false |
| `thinkbox_quick_action_research` | Think Box | bool | `True` | true / false | Think box quick action research. | profile | normal | false |
| `thinkbox_quick_action_clipboard` | Think Box | bool | `True` | true / false | Think box quick action clipboard. | profile | normal | false |
| `thinkbox_allow_no_focus_steal_toggle` | Think Box | bool | `True` | true / false | Think box allow no focus steal toggle. | profile | normal | false |
| `thinkbox_hide_when_main_focus` | Think Box | bool | `False` | true / false | Think box hide when main focus. | profile | normal | false |
| `thinkbox_remember_last_text` | Think Box | bool | `False` | true / false | Think box remember last text. | profile | normal | false |
| `thinkbox_clear_text_on_send` | Think Box | bool | `False` | true / false | Think box clear text on send. | profile | normal | false |
| `thinkbox_status_toast_seconds` | Think Box | int | `3` | integer (use safe/applicable range) | Think box status toast seconds. | profile | normal | false |
