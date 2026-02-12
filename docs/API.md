# API Contract (v1)

Base URL: `http://127.0.0.1:8000/api/v1`

## Health
- `GET /health`

## Model management
- `GET /models/sources`
- `POST /models/sources`
  - body: `{ name, base_url, auth_token? }`
- `POST /models/sources/{source_id}/test`
- `GET /models/options`

## Chat (SSE)
- `POST /agent/chat/stream`
  - body: `{ source_id, model, message, mode, context }`
  - headers: `X-Session-Id`
  - events:
    - `{"type":"token","content":"..."}`
    - `{"type":"permission_required","permission":"..."}`
    - `{"type":"manual_search_required","query":"...","instructions":"..."}`
    - `{"type":"fallback_mode","mode":"search_answer|remote_switch","reason":"..."}` 
    - `{"type":"error","detail":"..."}`

## Think Box (SSE)
- `POST /thinkbox/message`
  - body: `{ text, mode, toggles?, context?, model_source_id?, model? }`
  - modes: `screen_help | explain | steps | extract | research`
  - returns: `{ run_id }`
- `GET /thinkbox/stream?run_id=...&cursor=...`
  - headers: `X-Session-Id`
  - events:
    - `{"type":"run_started","run_id":"..."}`
    - `{"type":"token","content":"..."}`
    - `{"type":"error","detail":"..."}`
    - `{"type":"done"}`
- `POST /screen/capture`
  - body: `{ source: "active_window" | "region", region?, image_data_url? }`
  - permission: `screen.capture`
  - returns: `{ capture_id, timestamp, thumbnail_data_url? }`
- `POST /clipboard/read`
  - permission: `clipboard.read`
  - returns: `{ text }`
- `POST /clipboard/write`
  - body: `{ text }`
  - permission: `clipboard.write`
- `POST /files/search`
  - body: `{ path, pattern, max_results? }`
  - permission: `filesystem.read` (path-scoped)

## Permissions
- `POST /permissions/check`
- `POST /permissions/grant`
- `POST /permissions/revoke/{permission}`
- `GET /permissions/grants`

## Workflows
- `GET /workflows`
- `POST /workflows`
  - body: `{ id?, name, description, definition }`
- `POST /workflows/{workflow_id}/run`
  - body: `{ inputs }`

## Workspaces
- `GET /workspaces`
- `POST /workspaces`
  - body: `{ name, description?, scopes?, allowed_tools?, settings?, default_profile_id?, default_model_source_id?, default_model?, logging_strictness? }`
- `GET /workspaces/{id}`
- `PUT /workspaces/{id}`
- `POST /workspaces/{id}/activate`
- `DELETE /workspaces/{id}`

## Search
- `POST /search`
  - body: `{ query, num_results, safe, manual_payload? }`
- `POST /search/manual`
  - body: `{ query, json_results? , pasted_lines? }`
- `POST /search/test`

## Settings and secrets
- `GET /settings`
- `PATCH /settings`
- `GET /settings/registry`
- `POST /settings/secrets`
  - body: `{ key_name, value }`
- `GET /settings/secrets/{key_name}`

## Policy DSL
- `POST /policies/validate`
  - body: `{ text }`
- `POST /policies/test`
  - body: `{ action, confirmed? }`
- `GET /profiles`
- `POST /profiles`
  - body: `{ name, payload? }`
- `GET /profiles/{id}`
- `PUT /profiles/{id}`
  - body: `{ name?, payload }`
- `DELETE /profiles/{id}`
- `POST /profiles/{id}/activate`
- `POST /profiles/{id}/rollback`
- `POST /profiles/{id}/export`
- `POST /profiles/{id}/duplicate`
  - body: `{ name? }`
- `POST /profiles/import`
  - body: `{ name?, payload }`
- `POST /profiles/{id}/reset-category`
  - body: `{ keys: string[] }`

## Audit
- `GET /audit/logs`

## Runs / Replay
- `GET /runs`
- `GET /runs/{run_id}`
- `POST /runs/{run_id}/replay`

## Artifacts
- `GET /artifacts`
- `POST /artifacts`
  - body: `{ name, content, type, run_id?, metadata? }`
- `GET /artifacts/{id}`
- `DELETE /artifacts/{id}`

## Memory
- `GET /memory`
- `POST /memory`
- `GET /memory/{id}`
- `PUT /memory/{id}`
- `DELETE /memory/{id}`

## Plugins
- `GET /plugins`
- `POST /plugins/{id}/enable`

## Vector Index
- `POST /vector/index`
- `POST /vector/search`

## Diagnostics
- `POST /diagnostics/export`

## Security hardening (Windows)
- `GET /settings/security/network-lockdown/plan`
- `POST /settings/security/network-lockdown/apply`
- `GET /settings/security/network-lockdown/status`

## Ollama readiness
- `GET /ollama/status`
  - response: `{ installed, healthy, models_count, last_checked_at, next_check_in_seconds, fallback_mode_active, install_prompt_suppressed, install_prompt_suppressed_until }`
- `POST /ollama/install/prompt`
  - response: `{ launched, url, detail }`
- `POST /ollama/install/remind-later`
  - response: `{ status: "ok", remind_after_minutes }`

## UI replacement guide
Any frontend can replace the current Electron UI by:
1. Managing a session id client-side and sending it as `X-Session-Id`.
2. Calling REST endpoints above for CRUD/config workflows.
3. Consuming SSE from `/agent/chat/stream` for chat tokens/events.
4. For overlay/HUD clients, call `/thinkbox/message` + `/thinkbox/stream`, and request explicit permission grants before capture/clipboard/files actions.
