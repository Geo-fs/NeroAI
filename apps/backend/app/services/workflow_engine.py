"""Workflow persistence and execution engine with if/else support."""

from __future__ import annotations

import copy
import json
import re
import uuid
from typing import Any

from app.db.sqlite import connection
from app.models.schemas import WorkflowResponse, WorkflowSaveRequest
from app.services.agent_runtime import stream_chat
from app.services.expression_eval import evaluate_condition
from app.services.model_sources import list_model_options
from app.services.limits import build_run_limiter
from app.services.search_router import search_with_router
from app.services.settings_service import get_effective_settings
from app.services.tool_runner import run_tool
from app.services.run_logger import finish_run, log_run_event, start_run


def list_workflows() -> list[WorkflowResponse]:
    with connection() as conn:
        rows = conn.execute("SELECT id, name, description, definition_json FROM workflows ORDER BY updated_at DESC").fetchall()
    return [
        WorkflowResponse(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            definition=json.loads(row["definition_json"]),
        )
        for row in rows
    ]


def save_workflow(payload: WorkflowSaveRequest) -> WorkflowResponse:
    workflow_id = payload.id or str(uuid.uuid4())
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO workflows (id, name, description, definition_json, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description,
            definition_json=excluded.definition_json, updated_at=CURRENT_TIMESTAMP
            """,
            (workflow_id, payload.name, payload.description, json.dumps(payload.definition)),
        )
    return WorkflowResponse(id=workflow_id, name=payload.name, description=payload.description, definition=payload.definition)


def _lookup_path(path: str, context: dict[str, Any]) -> Any:
    parts = [p.strip() for p in path.split(".") if p.strip()]
    cur: Any = context
    for part in parts:
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _resolve_template(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k: _resolve_template(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_template(v, context) for v in value]
    if not isinstance(value, str):
        return value
    whole = re.fullmatch(r"\{\{\s*([^\}]+)\s*\}\}", value)
    if whole:
        return _lookup_path(whole.group(1), context)

    def repl(match: re.Match[str]) -> str:
        resolved = _lookup_path(match.group(1), context)
        return "" if resolved is None else str(resolved)

    return re.sub(r"\{\{\s*([^\}]+)\s*\}\}", repl, value)


async def _run_prompt(prompt: str, session_id: str, model_hint: dict[str, str] | None = None) -> str:
    options = await list_model_options()
    chosen = None
    if model_hint:
        chosen = next(
            (o for o in options if o.source_id == model_hint.get("source_id") and o.model == model_hint.get("model")),
            None,
        )
    if not chosen and options:
        chosen = options[0]
    if not chosen:
        return "No model source configured."
    event_payload = type(
        "WorkflowChatReq",
        (),
        {
            "source_id": chosen.source_id,
            "model": chosen.model,
            "message": prompt,
            "mode": "workflow",
            "context": {"safe_mode": False},
        },
    )()
    output = ""
    async for chunk in stream_chat(payload=event_payload, session_id=session_id):
        event = json.loads(chunk)
        if event.get("type") == "token":
            output += event.get("content", "")
    return output


async def _execute_steps(
    steps: list[dict[str, Any]],
    state: dict[str, Any],
    session_id: str,
    safe_mode: bool,
    limiter: RunLimiter,
    run_id: str,
) -> Any:
    returned = None
    for step in steps:
        step_id = step.get("id", f"step-{uuid.uuid4()}")
        step_type = step.get("type")
        if step_type == "set_var":
            name = step.get("name")
            value = _resolve_template(step.get("value"), state)
            state["vars"][name] = value
            log_run_event(run_id, "step.set_var", {"step": step_id, "name": name})
            continue

        if step_type == "prompt_agent":
            prompt = _resolve_template(step.get("prompt_template", ""), state)
            model_hint = _resolve_template(step.get("model"), state)
            output = await _run_prompt(prompt, session_id=session_id, model_hint=model_hint)
            state["vars"][step_id] = {"output": output}
            log_run_event(run_id, "step.prompt_agent", {"step": step_id})
            continue

        if step_type == "call_tool":
            tool_name = step.get("tool_name")
            input_template = _resolve_template(step.get("input_template", {}), state)
            if tool_name == "web_search":
                query = str(input_template.get("query", ""))
                result = await search_with_router(
                    query=query,
                    num_results=int(input_template.get("num_results", 5)),
                    safe=bool(input_template.get("safe", True)),
                    session_id=session_id,
                    safe_mode=safe_mode,
                    limiter=limiter,
                    run_id=run_id,
                )
                state["vars"][step_id] = result.model_dump()
            else:
                state["vars"][step_id] = run_tool(
                    tool=tool_name,
                    args=input_template,
                    session_id=session_id,
                    safe_mode=safe_mode,
                    mode="workflow",
                    limiter=limiter,
                    run_id=run_id,
                )
            log_run_event(run_id, "step.call_tool", {"step": step_id, "tool": tool_name})
            continue

        if step_type == "if":
            condition = str(step.get("condition", "False"))
            if evaluate_condition(condition, state):
                nested = step.get("then_steps", [])
            else:
                nested = step.get("else_steps", [])
            nested_result = await _execute_steps(nested, state, session_id=session_id, safe_mode=safe_mode, limiter=limiter, run_id=run_id)
            if nested_result is not None:
                returned = nested_result
                break
            continue

        if step_type == "loop":
            condition = str(step.get("condition", "True"))
            max_iter = int(step.get("max_iterations", 10))
            nested = step.get("steps", [])
            count = 0
            while count < max_iter and evaluate_condition(condition, state):
                count += 1
                nested_result = await _execute_steps(nested, state, session_id=session_id, safe_mode=safe_mode, limiter=limiter, run_id=run_id)
                if nested_result is not None:
                    returned = nested_result
                    break
            log_run_event(run_id, "step.loop", {"step": step_id, "iterations": count})
            if returned is not None:
                break
            continue

        if step_type == "return":
            returned = _resolve_template(step.get("value_template"), state)
            log_run_event(run_id, "step.return", {"step": step_id})
            break

    return returned


async def run_workflow(workflow: WorkflowResponse, inputs: dict[str, Any], session_id: str, safe_mode: bool = True) -> dict[str, Any]:
    definition = copy.deepcopy(workflow.definition)
    steps = definition.get("steps", [])
    state: dict[str, Any] = {"inputs": inputs, "vars": {}, "workflow": {"id": workflow.id, "name": workflow.name}}
    run = start_run(session_id=session_id, mode="workflow", input_text=json.dumps(inputs), model_source_id=None, model_name=None)
    settings = get_effective_settings()
    if settings.dry_run_mode == "always":
        plan = []
        for step in steps:
            plan.append({"id": step.get("id"), "type": step.get("type"), "tool": step.get("tool_name")})
        return {"inputs": inputs, "vars": {}, "return": {"dry_run": True, "plan": plan}, "run_id": run["id"]}
    limiter = build_run_limiter(
        {
            "max_tool_calls_per_message": settings.max_tool_calls_per_message,
            "max_tool_calls_per_minute": settings.max_tool_calls_per_minute,
            "max_files_read_per_run": settings.max_files_read_per_run,
            "max_bytes_read_per_run": settings.max_bytes_read_per_run,
            "max_runtime_seconds": settings.max_runtime_seconds,
        },
        session_id=session_id,
    )
    try:
        returned = await _execute_steps(steps, state, session_id=session_id, safe_mode=safe_mode, limiter=limiter, run_id=run["id"])
    finally:
        finish_run(run["id"], run["start"])
    return {"inputs": inputs, "vars": state["vars"], "return": returned, "run_id": run["id"]}
