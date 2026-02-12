"""HTTP API routes for NeroAI backend v1."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
import asyncio
import json
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    ChatRequest,
    GrantPermissionRequest,
    HealthResponse,
    ManualSearchSubmitRequest,
    ModelOptionResponse,
    ModelSourceCreate,
    ModelSourceResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionGrantResponse,
    SearchRequest,
    SearchResponse,
    RunResponse,
    RunDetailResponse,
    RunReplayResponse,
    ArtifactCreateRequest,
    ArtifactResponse,
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    PluginResponse,
    PluginToggleRequest,
    VectorIndexRequest,
    VectorSearchRequest,
    VectorSearchResponse,
    DiagnosticsExportResponse,
    SecurityLockdownResponse,
    SecurityPlanResponse,
    SecurityStatusResponse,
    OllamaInstallPromptResponse,
    OllamaRemindLaterResponse,
    OllamaStatusResponse,
    SecretSetRequest,
    SecretStatusResponse,
    PolicyValidateRequest,
    PolicyValidateResponse,
    PolicyTestRequest,
    PolicyTestResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsProfileCreateRequest,
    SettingsProfileUpdateRequest,
    SettingsProfileResponse,
    SettingsProfileExportResponse,
    SettingsProfileImportRequest,
    SettingsProfileDuplicateRequest,
    SettingsRegistryEntry,
    SourceTestResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
    WorkflowResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowSaveRequest,
    ThinkBoxMessageRequest,
    ThinkBoxMessageResponse,
    ScreenCaptureRequest,
    ScreenCaptureResponse,
    ClipboardWriteRequest,
    ClipboardReadResponse,
    FileSearchRequest,
    FileSearchResponse,
)
from app.services.agent_runtime import stream_chat
from app.services.audit import list_audit_logs
from app.services.limits import build_run_limiter
from app.services.model_sources import add_model_source, list_model_options, list_model_sources, test_model_source
from app.services.permission_broker import check_permission, grant_permission, list_grants, revoke_permission
from app.services.search_router import search_with_router, test_search_provider
from app.services.security_hardening import get_lockdown_status, get_security_plan, launch_lockdown_with_uac
from app.services.ollama_status import get_cached_ollama_status, record_install_prompt, remind_later
from app.services.secret_store import has_secret, set_secret
from app.services.settings_service import get_effective_settings, get_settings, update_settings
from app.services.policy_dsl import parse_policy
from app.services.policy_guard import policy_allows_action
from app.services.settings_profiles import (
    activate_profile,
    create_profile,
    delete_profile,
    duplicate_profile,
    export_profile,
    get_profile,
    import_profile,
    list_profiles,
    reset_category,
    rollback_profile,
    update_profile,
)
from app.services.settings_registry import registry_entries
from app.services.run_logger import get_run, list_runs
from app.services.artifacts import create_artifact, delete_artifact, get_artifact, list_artifacts
from app.services.memory import create_memory, delete_memory, get_memory, list_memory, update_memory
from app.services.plugins_service import list_plugins, set_plugin_enabled
from app.services.vector_index import index_documents, search_index, can_index_path
from app.services.diagnostics import export_diagnostics
from app.services.screen_capture import store_capture
from app.services.clipboard_service import read_clipboard, write_clipboard
from app.services.file_search import search_files
from app.services.thinkbox import read_thinkbox_stream, submit_thinkbox_message
from app.services.workspaces import (
    activate_workspace,
    create_workspace,
    delete_workspace,
    get_workspace,
    list_workspaces,
    update_workspace,
)
from app.services.workflow_engine import list_workflows, run_workflow, save_workflow
from app.services.policy_guard import assert_permission

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/models/options", response_model=list[ModelOptionResponse])
async def models_options() -> list[ModelOptionResponse]:
    return await list_model_options()


@router.get("/models/sources", response_model=list[ModelSourceResponse])
def sources() -> list[ModelSourceResponse]:
    return list_model_sources()


@router.post("/models/sources", response_model=ModelSourceResponse)
def create_source(payload: ModelSourceCreate) -> ModelSourceResponse:
    return add_model_source(payload)


@router.post("/models/sources/{source_id}/test", response_model=SourceTestResponse)
async def source_test(source_id: str) -> SourceTestResponse:
    return await test_model_source(source_id)


@router.post("/agent/chat/stream")
async def agent_stream(payload: ChatRequest, x_session_id: str = Header(default="default")) -> StreamingResponse:
    async def event_stream():
        async for chunk in stream_chat(payload, session_id=x_session_id):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/thinkbox/message", response_model=ThinkBoxMessageResponse)
async def thinkbox_message(payload: ThinkBoxMessageRequest, x_session_id: str = Header(default="default")) -> ThinkBoxMessageResponse:
    run_id = await submit_thinkbox_message(payload, session_id=x_session_id)
    return ThinkBoxMessageResponse(run_id=run_id)


@router.get("/thinkbox/stream")
async def thinkbox_stream(run_id: str, cursor: int = 0) -> StreamingResponse:
    async def event_stream():
        current = cursor
        for _ in range(1200):  # up to ~120s
            events, current, done = read_thinkbox_stream(run_id, current)
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
            if done:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
            await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/permissions/check", response_model=PermissionCheckResponse)
def permission_check(payload: PermissionCheckRequest, x_session_id: str = Header(default="default")) -> PermissionCheckResponse:
    granted, reason = check_permission(payload.permission, session_id=x_session_id, path=payload.path)
    return PermissionCheckResponse(granted=granted, reason=reason)


@router.post("/permissions/grant", response_model=PermissionGrantResponse)
def permission_grant(payload: GrantPermissionRequest, x_session_id: str = Header(default="default")) -> PermissionGrantResponse:
    grant_permission(payload, session_id=x_session_id)
    return PermissionGrantResponse(
        permission=payload.permission,
        scope=payload.scope,
        session_id=None if payload.scope == "always" else x_session_id,
        allowed_paths=payload.allowed_paths,
    )


@router.post("/permissions/revoke/{permission}", response_model=HealthResponse)
def permission_revoke(permission: str, x_session_id: str = Header(default="default")) -> HealthResponse:
    revoke_permission(permission, session_id=x_session_id)
    return HealthResponse()


@router.get("/permissions/grants", response_model=list[PermissionGrantResponse])
def permission_grants(x_session_id: str = Header(default="default")) -> list[PermissionGrantResponse]:
    return list_grants(session_id=x_session_id)


@router.post("/screen/capture", response_model=ScreenCaptureResponse)
def screen_capture(payload: ScreenCaptureRequest, x_session_id: str = Header(default="default")) -> ScreenCaptureResponse:
    settings = get_effective_settings()
    try:
        assert_permission("screen.capture", session_id=x_session_id, safe_mode=settings.safe_mode_default)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    saved = store_capture(
        source=payload.source,
        image_data_url=payload.image_data_url,
        region=payload.region.model_dump() if payload.region else None,
        store_thumbnail=settings.thinkbox_store_thumbnail,
    )
    return ScreenCaptureResponse(
        capture_id=saved["capture_id"],
        timestamp=saved["timestamp"],
        thumbnail_data_url=saved.get("thumbnail_data_url"),
    )


@router.post("/clipboard/read", response_model=ClipboardReadResponse)
def clipboard_read(x_session_id: str = Header(default="default")) -> ClipboardReadResponse:
    settings = get_effective_settings()
    try:
        assert_permission("clipboard.read", session_id=x_session_id, safe_mode=settings.safe_mode_default)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ClipboardReadResponse(text=read_clipboard())


@router.post("/clipboard/write", response_model=HealthResponse)
def clipboard_write(payload: ClipboardWriteRequest, x_session_id: str = Header(default="default")) -> HealthResponse:
    settings = get_effective_settings()
    try:
        assert_permission("clipboard.write", session_id=x_session_id, safe_mode=settings.safe_mode_default)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    write_clipboard(payload.text)
    return HealthResponse()


@router.post("/files/search", response_model=FileSearchResponse)
def files_search(payload: FileSearchRequest, x_session_id: str = Header(default="default")) -> FileSearchResponse:
    settings = get_effective_settings()
    try:
        assert_permission("filesystem.read", session_id=x_session_id, safe_mode=settings.safe_mode_default, path=payload.path)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    results = search_files(path=payload.path, pattern=payload.pattern, max_results=payload.max_results)
    return FileSearchResponse(results=results)


@router.get("/audit/logs")
def audit_logs() -> list[dict]:
    return list_audit_logs(limit=200)


@router.get("/runs", response_model=list[RunResponse])
def runs_list() -> list[RunResponse]:
    return [RunResponse(**row) for row in list_runs(limit=100)]


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def runs_get(run_id: str) -> RunDetailResponse:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunDetailResponse(**run)


@router.post("/runs/{run_id}/replay", response_model=RunReplayResponse)
def runs_replay(run_id: str) -> RunReplayResponse:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    steps = run.get("events", [])
    return RunReplayResponse(run_id=run_id, steps=steps)


@router.get("/artifacts", response_model=list[ArtifactResponse])
def artifacts_list() -> list[ArtifactResponse]:
    return [ArtifactResponse(**row) for row in list_artifacts(limit=200)]


@router.post("/artifacts", response_model=ArtifactResponse)
def artifacts_create(payload: ArtifactCreateRequest) -> ArtifactResponse:
    item = create_artifact(
        name=payload.name,
        content=payload.content,
        artifact_type=payload.type,
        run_id=payload.run_id,
        metadata=payload.metadata,
    )
    return ArtifactResponse(**item)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
def artifacts_get(artifact_id: str) -> ArtifactResponse:
    item = get_artifact(artifact_id)
    if not item:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactResponse(**item)


@router.delete("/artifacts/{artifact_id}", response_model=HealthResponse)
def artifacts_delete(artifact_id: str) -> HealthResponse:
    delete_artifact(artifact_id)
    return HealthResponse()


@router.get("/memory", response_model=list[MemoryResponse])
def memory_list() -> list[MemoryResponse]:
    return [MemoryResponse(**row) for row in list_memory()]


@router.post("/memory", response_model=MemoryResponse)
def memory_create(payload: MemoryCreateRequest) -> MemoryResponse:
    item = create_memory(payload.kind, payload.content)
    return MemoryResponse(**item)


@router.get("/memory/{memory_id}", response_model=MemoryResponse)
def memory_get(memory_id: str) -> MemoryResponse:
    item = get_memory(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryResponse(**item)


@router.put("/memory/{memory_id}", response_model=MemoryResponse)
def memory_update(memory_id: str, payload: MemoryUpdateRequest) -> MemoryResponse:
    item = update_memory(memory_id, payload.content)
    return MemoryResponse(**item)


@router.delete("/memory/{memory_id}", response_model=HealthResponse)
def memory_delete(memory_id: str) -> HealthResponse:
    delete_memory(memory_id)
    return HealthResponse()


@router.get("/plugins", response_model=list[PluginResponse])
def plugins_list() -> list[PluginResponse]:
    return [PluginResponse(**row) for row in list_plugins()]


@router.post("/plugins/{plugin_id}/enable", response_model=HealthResponse)
def plugins_enable(plugin_id: str, payload: PluginToggleRequest) -> HealthResponse:
    set_plugin_enabled(plugin_id, payload.enabled)
    return HealthResponse()


@router.post("/vector/index", response_model=HealthResponse)
def vector_index(payload: VectorIndexRequest) -> HealthResponse:
    items = [item.model_dump() for item in payload.items if can_index_path(item.path)]
    index_documents(payload.workspace_id, items)
    return HealthResponse()


@router.post("/vector/search", response_model=VectorSearchResponse)
def vector_search(payload: VectorSearchRequest) -> VectorSearchResponse:
    results = search_index(payload.workspace_id, payload.query, payload.limit)
    return VectorSearchResponse(results=results)


@router.post("/diagnostics/export", response_model=DiagnosticsExportResponse)
def diagnostics_export() -> DiagnosticsExportResponse:
    path = export_diagnostics()
    return DiagnosticsExportResponse(path=path)


@router.get("/workspaces", response_model=list[WorkspaceResponse])
def workspaces_list() -> list[WorkspaceResponse]:
    return [WorkspaceResponse(**row) for row in list_workspaces()]


@router.post("/workspaces", response_model=WorkspaceResponse)
def workspaces_create(payload: WorkspaceCreateRequest) -> WorkspaceResponse:
    workspace = create_workspace(
        name=payload.name,
        description=payload.description or "",
        scopes=payload.scopes,
        allowed_tools=payload.allowed_tools,
        settings=payload.settings,
        default_profile_id=payload.default_profile_id,
        default_model_source_id=payload.default_model_source_id,
        default_model=payload.default_model,
        logging_strictness=payload.logging_strictness,
    )
    return WorkspaceResponse(**workspace)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def workspaces_get(workspace_id: str) -> WorkspaceResponse:
    workspace = get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**workspace)


@router.put("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def workspaces_update(workspace_id: str, payload: WorkspaceUpdateRequest) -> WorkspaceResponse:
    workspace = update_workspace(
        workspace_id=workspace_id,
        name=payload.name,
        description=payload.description,
        scopes=payload.scopes,
        allowed_tools=payload.allowed_tools,
        settings=payload.settings,
        default_profile_id=payload.default_profile_id,
        default_model_source_id=payload.default_model_source_id,
        default_model=payload.default_model,
        logging_strictness=payload.logging_strictness,
    )
    return WorkspaceResponse(**workspace)


@router.post("/workspaces/{workspace_id}/activate", response_model=WorkspaceResponse)
def workspaces_activate(workspace_id: str) -> WorkspaceResponse:
    workspace = activate_workspace(workspace_id)
    return WorkspaceResponse(**workspace)


@router.delete("/workspaces/{workspace_id}", response_model=HealthResponse)
def workspaces_delete(workspace_id: str) -> HealthResponse:
    delete_workspace(workspace_id)
    return HealthResponse()


@router.get("/workflows", response_model=list[WorkflowResponse])
def workflows() -> list[WorkflowResponse]:
    return list_workflows()


@router.post("/workflows", response_model=WorkflowResponse)
def workflow_save(payload: WorkflowSaveRequest) -> WorkflowResponse:
    return save_workflow(payload)


@router.post("/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
async def workflow_run(workflow_id: str, payload: WorkflowRunRequest, x_session_id: str = Header(default="default")) -> WorkflowRunResponse:
    workflow = next((item for item in list_workflows() if item.id == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    settings = get_settings()
    result = await run_workflow(workflow, payload.inputs, session_id=x_session_id, safe_mode=settings.safe_mode_default)
    run_id = result.get("run_id")
    return WorkflowRunResponse(result=result, run_id=run_id)


@router.get("/settings", response_model=SettingsResponse)
def read_settings() -> SettingsResponse:
    return get_settings()


@router.patch("/settings", response_model=SettingsResponse)
def patch_settings(payload: SettingsUpdateRequest) -> SettingsResponse:
    return update_settings(payload)


@router.get("/settings/registry", response_model=list[SettingsRegistryEntry])
def settings_registry() -> list[SettingsRegistryEntry]:
    return [SettingsRegistryEntry(**item) for item in registry_entries()]


@router.get("/profiles", response_model=list[SettingsProfileResponse])
def profiles_list() -> list[SettingsProfileResponse]:
    return [SettingsProfileResponse(**row) for row in list_profiles()]


@router.post("/profiles", response_model=SettingsProfileResponse)
def profiles_create(payload: SettingsProfileCreateRequest) -> SettingsProfileResponse:
    profile = create_profile(payload.name, payload.payload or {})
    return SettingsProfileResponse(**profile)


@router.get("/profiles/{profile_id}", response_model=SettingsProfileResponse)
def profiles_get(profile_id: str) -> SettingsProfileResponse:
    profile = get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return SettingsProfileResponse(**profile)


@router.put("/profiles/{profile_id}", response_model=SettingsProfileResponse)
def profiles_update(profile_id: str, payload: SettingsProfileUpdateRequest) -> SettingsProfileResponse:
    profile = update_profile(profile_id, payload.payload, name=payload.name)
    return SettingsProfileResponse(**profile)


@router.post("/profiles/{profile_id}/duplicate", response_model=SettingsProfileResponse)
def profiles_duplicate(profile_id: str, payload: SettingsProfileDuplicateRequest) -> SettingsProfileResponse:
    name = payload.name or "Copy of " + profile_id[:8]
    profile = duplicate_profile(profile_id, new_name=name)
    return SettingsProfileResponse(**profile)


@router.post("/profiles/{profile_id}/activate", response_model=SettingsProfileResponse)
def profiles_activate(profile_id: str) -> SettingsProfileResponse:
    profile = activate_profile(profile_id)
    return SettingsProfileResponse(**profile)


@router.post("/profiles/{profile_id}/rollback", response_model=SettingsProfileResponse)
def profiles_rollback(profile_id: str) -> SettingsProfileResponse:
    profile = rollback_profile(profile_id)
    return SettingsProfileResponse(**profile)


@router.post("/profiles/{profile_id}/export", response_model=SettingsProfileExportResponse)
def profiles_export(profile_id: str) -> SettingsProfileExportResponse:
    data = export_profile(profile_id)
    return SettingsProfileExportResponse(**data)


@router.post("/profiles/import", response_model=SettingsProfileResponse)
def profiles_import(payload: SettingsProfileImportRequest) -> SettingsProfileResponse:
    profile = import_profile({"name": payload.name, "payload": payload.payload})
    return SettingsProfileResponse(**profile)


@router.post("/profiles/{profile_id}/reset-category", response_model=SettingsProfileResponse)
def profiles_reset_category(profile_id: str, payload: dict) -> SettingsProfileResponse:
    keys = payload.get("keys", [])
    profile = reset_category(profile_id, keys)
    return SettingsProfileResponse(**profile)


@router.delete("/profiles/{profile_id}", response_model=HealthResponse)
def profiles_delete(profile_id: str) -> HealthResponse:
    delete_profile(profile_id)
    return HealthResponse()


@router.post("/settings/secrets", response_model=SecretStatusResponse)
def upsert_secret(payload: SecretSetRequest) -> SecretStatusResponse:
    set_secret(payload.key_name, payload.value)
    return SecretStatusResponse(key_name=payload.key_name, configured=True)


@router.get("/settings/secrets/{key_name}", response_model=SecretStatusResponse)
def secret_status(key_name: str) -> SecretStatusResponse:
    return SecretStatusResponse(key_name=key_name, configured=has_secret(key_name))


@router.post("/policies/validate", response_model=PolicyValidateResponse)
def policy_validate(payload: PolicyValidateRequest) -> PolicyValidateResponse:
    parsed = parse_policy(payload.text or "")
    return PolicyValidateResponse(ok=len(parsed.errors) == 0, errors=parsed.errors)


@router.post("/policies/test", response_model=PolicyTestResponse)
def policy_test(payload: PolicyTestRequest) -> PolicyTestResponse:
    allowed, reason = policy_allows_action(payload.action, confirmed=payload.confirmed)
    return PolicyTestResponse(allowed=allowed, reason=reason)


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest, x_session_id: str = Header(default="default")) -> SearchResponse:
    settings = get_effective_settings()
    limiter = build_run_limiter(
        {
            "max_tool_calls_per_message": settings.max_tool_calls_per_message,
            "max_tool_calls_per_minute": settings.max_tool_calls_per_minute,
            "max_files_read_per_run": settings.max_files_read_per_run,
            "max_bytes_read_per_run": settings.max_bytes_read_per_run,
            "max_runtime_seconds": settings.max_runtime_seconds,
        },
        session_id=x_session_id,
    )
    return await search_with_router(
        query=payload.query,
        num_results=payload.num_results,
        safe=payload.safe,
        session_id=x_session_id,
        manual_payload=payload.manual_payload,
        safe_mode=settings.safe_mode_default,
        limiter=limiter,
    )


@router.post("/search/test", response_model=SearchResponse)
async def test_search(x_session_id: str = Header(default="default")) -> SearchResponse:
    return await test_search_provider(session_id=x_session_id)


@router.post("/search/manual", response_model=SearchResponse)
async def manual_search(payload: ManualSearchSubmitRequest, x_session_id: str = Header(default="default")) -> SearchResponse:
    settings = get_effective_settings()
    limiter = build_run_limiter(
        {
            "max_tool_calls_per_message": settings.max_tool_calls_per_message,
            "max_tool_calls_per_minute": settings.max_tool_calls_per_minute,
            "max_files_read_per_run": settings.max_files_read_per_run,
            "max_bytes_read_per_run": settings.max_bytes_read_per_run,
            "max_runtime_seconds": settings.max_runtime_seconds,
        },
        session_id=x_session_id,
    )
    return await search_with_router(
        query=payload.query,
        num_results=10,
        safe=True,
        session_id=x_session_id,
        manual_payload=payload,
        safe_mode=settings.safe_mode_default,
        limiter=limiter,
    )


@router.get("/settings/security/network-lockdown/plan", response_model=SecurityPlanResponse)
def security_plan() -> SecurityPlanResponse:
    return get_security_plan()


@router.post("/settings/security/network-lockdown/apply", response_model=SecurityLockdownResponse)
def security_apply() -> SecurityLockdownResponse:
    return launch_lockdown_with_uac()


@router.get("/settings/security/network-lockdown/status", response_model=SecurityStatusResponse)
def security_status() -> SecurityStatusResponse:
    return get_lockdown_status()


@router.get("/ollama/status", response_model=OllamaStatusResponse)
def ollama_status() -> OllamaStatusResponse:
    return OllamaStatusResponse(**get_cached_ollama_status())


@router.post("/ollama/install/prompt", response_model=OllamaInstallPromptResponse)
def ollama_install_prompt() -> OllamaInstallPromptResponse:
    return OllamaInstallPromptResponse(**record_install_prompt())


@router.post("/ollama/install/remind-later", response_model=OllamaRemindLaterResponse)
def ollama_remind_later() -> OllamaRemindLaterResponse:
    minutes = int(get_effective_settings().ollama_remind_later_minutes)
    result = remind_later(minutes)
    return OllamaRemindLaterResponse(**result)
