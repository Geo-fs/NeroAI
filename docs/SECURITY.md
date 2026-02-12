# Security Model

## Core guarantees
- Default deny permissions are enforced outside model outputs.
- Safe Mode defaults ON and blocks external permissions (`web.search`, clipboard, process).
- Safe Mode defaults ON and blocks `screen.capture` as well.
- Tool execution is isolated in a subprocess with strict policy checks.
- Secrets are encrypted at rest and never logged in plaintext.

## Permission enforcement
1. Runtime/workflow requests tool or web search action.
2. `policy_guard` verifies permission and Safe Mode.
3. `permission_broker` verifies grant scope and path scopes.
4. Denials are logged as audit events.
5. Think Box capture/clipboard/files APIs enforce the same broker and Safe Mode checks.

## Screen capture handling
- `screen.capture` is permission-gated (default scope expectation: once).
- Captures are ephemeral (`services/screen_capture.py`) with TTL cleanup.
- By default only last capture ID is retained in memory; long-term screenshot storage is off by default.

## Tool runner hardening
- Timeout per call (default 30s).
- Stdout/stderr capture size limited (default 256 KB) with truncation marker.
- Minimal environment allowlist passed to subprocess.
- Dedicated working directory under `apps/backend/tool_runs`.
- Path scoping uses normalized resolved paths and blocks out-of-scope access.
- Reparse-point/junction checks reduce symlink escape risk on Windows.
- Networked search is intentionally **not** executed in tool runner.
- Quarantine Mode (default ON): out-of-workspace files are copied to a temporary quarantine directory before reads.
- File writes default to preview-only unless explicitly confirmed.

## Network policy
- File tools (`file_read`, `file_write`, `file_list`, `file_read_batch`) run in tool runner.
- `web.search` runs in backend service layer only (`search_router`), permission-gated.
- No claim is made of OS-grade network sandboxing for subprocesses.
- Optional OS-level hardening is available on Windows:
  - Firewall rule name: `NeroAI Tool Runner - Block Outbound`
  - Target program: tool runner executable path (same interpreter used by `tool_worker`)
  - Direction: `Outbound`
  - Action: `Block`
  - Profile: `Any`

### Managing the firewall hardening rule
- Create (from UI): `Settings -> Security Hardening -> Lock Down Tool Runner Network`
- Verify (from UI): `Check Status`
  - Network blocking is only considered active when `confirmed_blocking=true`.
- Remove manually (PowerShell):
```powershell
netsh advfirewall firewall delete rule name="NeroAI Tool Runner - Block Outbound"
```

## Search privacy logging
- Always logged: provider, query hash, timestamp, success/failure, result count.
- Raw query text is stored only when:
  - Privacy Mode is OFF, and
  - `allow_query_text_logging` is ON.
- Full HTML pages are never stored.

## Audit redaction
- Tool input/output logs store hashes by default.
- Verbose mode optionally stores short truncated samples.
- Key-like fields (`token`, `secret`, `auth`, `api_key`, etc.) are redacted.

## Diagnostics bundle
- Export includes redacted logs, settings profiles (no secrets), and run metadata.
- Secrets and raw sensitive content are excluded by default.

## Current limitations
- Subprocess boundary is best-effort isolation, not a full OS sandbox.
- LocalBrowserProvider can hit CAPTCHA/bot checks and may require manual fallback.
- Junction/reparse handling is defensive but not equivalent to kernel-level sandboxing.
