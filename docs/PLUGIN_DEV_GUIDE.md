# Plugin Developer Guide (Stub)

## Plugin interface
Each backend plugin must define:
- `name`
- `description`
- `input_schema`
- `permission_requirements`
- `run(payload) -> dict`

## Steps
1. Create plugin file in `apps/backend/app/plugins/`.
2. Add permission requirements in plugin metadata.
3. Register plugin instance in `registry.py`.
4. Update workflow/editor UX if plugin should be user-accessible.
5. Add tests for permission behavior and path handling.

## Security checklist
- Avoid shell execution unless explicitly permissioned.
- Validate inputs strictly.
- Never write outside approved scopes.
- Log minimal metadata only.
