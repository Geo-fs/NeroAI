# GitHub Setup Checklist

Use this checklist before making the repository public.

## 1) Repository hygiene
- Ensure `.gitignore` is up to date (build outputs, virtual envs, DB, secrets).
- Confirm no tracked local runtime files:
  - `apps/backend/neroai.db`
  - `apps/desktop/release/`
  - `apps/desktop/dist/`
  - `.env*`
- Remove personal paths or machine-specific notes from docs.

## 2) Secrets and credentials
- Rotate any tokens used during development.
- Verify no secrets in tracked code history.
- Keep secret values only in runtime settings/secret store.

## 3) Required top-level docs
- `README.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/ERROR_HELP.md`
- `docs/UI_SETTINGS.md`

Optional but recommended:
- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md` (GitHub advisory/contact policy)

## 4) Build and test validation
- Backend tests:
  - `npm run test:backend`
- Build:
  - `npm run build`
- Smoke run:
  - `npm run dev`

## 5) GitHub repository settings
- Enable branch protection on `main`.
- Enable secret scanning and dependency alerts.
- Configure issue templates and PR template (optional).
- Add a release process (tags/changelog).

## 6) Suggested CI (later)
- Python backend test job
- Node build job
- Optional lint/typecheck jobs

## 7) First public release checklist
- Add license text
- Create initial tag (for example `v0.1.0`)
- Publish release notes
- Attach installer artifact if needed
