# NeroAI

NeroAI is a Windows-first, backend-driven agent platform with an Electron desktop client and FastAPI local service.  
It is designed for secure tool use, modular growth, and UI replaceability.

## Highlights
- Local + remote Ollama-compatible model sources
- Permission-gated tools (default-deny, path-scoped where applicable)
- Safe Mode defaults ON
- Search provider routing with privacy-aware logging
- Think Box overlay (global hotkey, screen-help workflows)
- Settings registry with profile/workspace overrides
- Audit, runs/replay, artifacts, memory, policy DSL

## Monorepo Structure
```text
/apps
  /desktop      Electron + React UI shell
  /backend      FastAPI orchestration service + SQLite
/packages
  /core         shared types/schema utilities
  /plugins      plugin interfaces
/docs           architecture, security, API, settings, troubleshooting
```

## Prerequisites
- Windows 11
- Node.js 20+
- Python 3.10+ (3.11+ recommended)
- Optional but recommended for local models: Ollama (`https://ollama.com/download/windows`)

## Quick Start (Development)
```powershell
npm install
cd apps/backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
cd ..\..
npm run dev
```

## Build Installer
```powershell
npm run build
```
Output:
- `apps/desktop/release/NeroAI Setup 0.1.0.exe`

## Core Runtime Behavior
- Backend API base: `http://127.0.0.1:8000/api/v1`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Chat streaming uses SSE
- Think Box uses dedicated message/stream endpoints
- If local Ollama is unavailable, runtime fallback can switch to remote models or web-search answer mode based on settings

## Main Desktop Areas
- `Chat`
- `Permissions`
- `Workflows`
- `Audit`
- `Settings`

## Documentation Index
- `CONTRIBUTING.md` contribution workflow and PR expectations
- `docs/README.md` docs map
- `docs/API.md` API contract and event formats
- `docs/ARCHITECTURE.md` module boundaries and data model
- `docs/SECURITY.md` threat model, policy, hardening
- `docs/UI_SETTINGS.md` full UI/UX setting catalog
- `docs/ERROR_HELP.md` troubleshooting and common fixes
- `docs/GITHUB_SETUP.md` publishing and repo hygiene checklist

## Security Notes
- Secrets are stored encrypted at rest by backend service.
- Do not commit `.env` files, local databases, or build outputs.
- Firewall lock claims are only valid when status endpoint confirms blocking.

## Useful Commands
```powershell
# Backend tests
npm run test:backend

# Full build
npm run build

# Dev stack (backend + desktop)
npm run dev
```

## Known Operational Limitations
- Some constrained/sandboxed environments can fail with `spawn EPERM` for build/dev child processes.
- Local browser search providers may hit CAPTCHA and require manual fallback.
- OS-level firewall lock requires admin privileges and explicit verification.
