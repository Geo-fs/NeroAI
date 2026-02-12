# Contributing to NeroAI

Thanks for contributing.

## Development setup
1. Install prerequisites (Node, Python, optional Ollama).
2. Install dependencies:
   - `npm install`
   - `cd apps/backend`
   - `python -m venv .venv`
   - `.\.venv\Scripts\python -m pip install -r requirements.txt`
3. Start dev stack:
   - `cd ..\..`
   - `npm run dev`

## Code expectations
- Keep backend logic in `apps/backend` (API-first architecture).
- Keep frontend as thin client where possible.
- Respect security defaults:
  - default-deny permissions
  - Safe Mode default ON
  - do not bypass policy guard
- Add tests for load-bearing changes.

## Test before PR
- `npm run test:backend`
- `npm run build`

## PR guidance
- Keep scope focused.
- Document API or behavior changes in docs.
- Include migration notes if settings/schema behavior changes.
