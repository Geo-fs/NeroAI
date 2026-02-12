# Architecture

## Overview
NeroAI is split into a replaceable UI shell and a backend-first orchestration service. The desktop app is a thin HTTP/SSE client.

## Runtime topology
- `apps/desktop`: Electron shell + React tabs (Chat, Permissions, Workflows, Audit, Settings).
- `apps/desktop`: includes a secondary frameless Think Box overlay window toggled by global hotkey.
- `apps/backend`: FastAPI service with versioned API under `/api/v1`.
- `apps/backend/neroai.db`: SQLite persistence.

## Backend module boundaries
- `api/routes.py`: stable API contract layer (Pydantic models only).
- `services/agent_runtime.py`: chat orchestration + SSE token streaming.
- `services/model_sources.py`: local/remote Ollama source management.
- `services/ollama_status.py`: first-run and background local Ollama readiness checks + prompt snooze state.
- `services/runtime_fallback.py`: runtime routing between local model, remote source switch, and search-answer fallback.
- `services/search_router.py`: provider routing and fallback orchestration.
- `services/search_providers.py`: DuckDuckGo HTML, Local Browser (Playwright), Manual fallback.
- `services/permission_broker.py` + `services/policy_guard.py`: default-deny permission enforcement outside LLM.
- `services/policy_dsl.py`: policy-as-code parser and evaluator.
- `services/limits.py`: per-run limits and budgets enforcement.
- `services/workspaces.py`: workspace CRUD, scopes, tool allowlist, and overrides.
- `services/tool_runner.py`: hardened subprocess tool execution for local file tools.
- `services/workflow_engine.py`: JSON workflow runtime with step types + if/else branching.
- `services/secret_store.py`: encrypted at-rest secret storage (Fernet).
- `services/settings_registry.py`: authoritative settings keys, defaults, validation.
- `services/settings_service.py`: global settings persistence and safe defaults enforcement.
- `services/settings_profiles.py`: versioned settings profiles with history snapshots + rollback.
- `services/audit.py`: redacted audit logging.
- `services/run_logger.py`: session replay and run report logging.
- `services/artifacts.py`: persisted output artifacts.
- `services/memory.py`: structured memory store.
- `services/plugins_local.py` + `services/plugins_service.py`: local plugin loading and enablement.
- `services/vector_index.py`: local TF-like indexing and retrieval.
- `services/diagnostics.py`: sanitized diagnostics export.
- `services/intent_router.py`: heuristic intent routing.
- `services/thinkbox.py`: compact HUD request orchestration and SSE stream cache.
- `services/screen_capture.py`: ephemeral capture IDs with TTL cleanup.
- `services/clipboard_service.py`: backend clipboard read/write operations.

## Data model summary
- `model_sources`: Ollama endpoints metadata.
- `app_settings`: also stores runtime state values like Ollama install prompt snooze.
- `permission_grants`: session/global permission grants and path scopes.
- `workflows`: workflow definitions as JSON.
- `audit_logs`: privacy-aware event logs.
- `app_settings`: user behavior and security toggles.
- `profiles`: settings profile metadata (name, version, active).
- `profile_settings`: per-profile key/value overrides.
- `profile_history`: last-known-good snapshots for rollback.
- `secrets`: encrypted credentials/tokens.
- `workspaces`: workspace definitions and defaults.
- `workspace_scopes`: allowed folder scopes per workspace.
- `workspace_tools`: tool allowlist per workspace.
- `workspace_settings`: per-workspace overrides.
- `runs` + `run_events`: session replay data.
- `artifacts`: saved outputs.
- `memory_items`: structured memory.
- `plugin_registry`: local plugin records.
- `vector_index`: local retrieval index.

## UI replacement strategy
- A new UI can fully replace `apps/desktop` by calling `/api/v1`.
- Business logic is intentionally centralized in backend services.
- SSE chat contract is stable (`/api/v1/agent/chat/stream` emits `token`, `permission_required`, `manual_search_required`, `error` events).
- Think Box/HUD clients can use `/api/v1/thinkbox/message` + `/api/v1/thinkbox/stream` without backend changes.
