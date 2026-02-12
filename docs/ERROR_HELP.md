# NeroAI Error Help

This guide lists common runtime issues, likely causes, and exact fixes.

## App shows blank or white window
- Symptoms:
  - desktop app opens but content is blank
  - devtools reports missing `assets/*.js` or `assets/*.css`
- Likely cause:
  - stale/partial desktop build output
- Fix:
  1. Run `npm run build` from repo root.
  2. Re-launch `apps/desktop/release/win-unpacked/NeroAI.exe`.
  3. If still blank, run `npm run dev` and inspect console output.

## Backend not reachable
- Symptoms:
  - UI errors with fetch failures to `http://127.0.0.1:8000`
  - startup loading screen hangs
- Fix:
  1. Verify backend venv exists at `apps/backend/.venv`.
  2. Install requirements:
     - `cd apps/backend`
     - `.\.venv\Scripts\python -m pip install -r requirements.txt`
  3. Run backend directly:
     - `.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

## Ollama not detected / fallback mode active
- Symptoms:
  - banner: `Ollama Not Available`
  - chat emits fallback events and uses web-search fallback
- Fix:
  1. Install Ollama: `https://ollama.com/download/windows`
  2. Start Ollama and verify:
     - open `http://127.0.0.1:11434/api/tags`
  3. Wait one poll interval (default 10s) or refresh app.

## Think Box hotkey not working
- Symptoms:
  - pressing configured hotkey does nothing
- Likely cause:
  - hotkey conflict with another app
- Fix:
  1. Open `Settings -> UI`.
  2. Change `thinkbox_hotkey`.
  3. Apply settings and verify hotkey status message.

## Permission denied errors for capture/clipboard/files/search
- Symptoms:
  - API returns permission required/403
- Fix:
  1. Grant required permission in `Permissions` tab (`once/session/always`).
  2. Ensure Safe Mode setting is appropriate for the action.
  3. For filesystem actions, confirm path is within granted scope/workspace scope.

## Search returns manual fallback often
- Symptoms:
  - `manual_required` responses from search endpoints
- Likely cause:
  - provider blocked or network unavailable
- Fix:
  1. In `Settings -> Search`, test provider.
  2. Enable Local Browser provider if available.
  3. Use manual fallback input (`title|url|snippet` lines).

## Build fails with `spawn EPERM` in constrained environment
- Symptoms:
  - `tsup`/`esbuild` spawn EPERM during `npm run build`
- Fix:
  1. Re-run command in normal local shell outside sandbox restrictions.
  2. Confirm antivirus policy is not blocking Node child process execution.

## Firewall lock says not confirmed
- Symptoms:
  - security status shows `confirmed_blocking=false`
- Fix:
  1. Run `Settings -> Security Hardening -> Check Status`.
  2. If needed, apply lock with admin prompt.
  3. Verify rule exists:
     - `NeroAI Tool Runner - Block Outbound`

## Tests fail after schema changes
- Fix:
  1. Run backend tests from `apps/backend`:
     - `.\.venv\Scripts\python -m pytest`
  2. If failures mention unknown settings keys, update:
     - `app/services/settings_registry.py`
     - `app/models/schemas.py`
     - frontend `src/api.ts` settings type.
