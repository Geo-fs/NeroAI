"""Model source registry and Ollama model discovery."""

from __future__ import annotations

import uuid

import httpx

from app.db.sqlite import connection
from app.models.schemas import ModelOptionResponse, ModelSourceCreate, ModelSourceResponse, SourceTestResponse
from app.services.audit import log_event
from app.services.secret_store import get_secret, has_secret, set_secret


def list_model_sources() -> list[ModelSourceResponse]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, name, base_url, is_local, created_at FROM model_sources ORDER BY created_at DESC"
        ).fetchall()
    return [
        ModelSourceResponse(
            id=row["id"],
            name=row["name"],
            base_url=row["base_url"],
            is_local=bool(row["is_local"]),
            has_auth_token=has_secret(f"model_source:{row['id']}:auth_token"),
            created_at=row["created_at"],
        )
        for row in rows
    ]


def add_model_source(payload: ModelSourceCreate) -> ModelSourceResponse:
    source_id = str(uuid.uuid4())
    with connection() as conn:
        conn.execute(
            "INSERT INTO model_sources (id, name, base_url, is_local) VALUES (?, ?, ?, 0)",
            (source_id, payload.name, payload.base_url.rstrip("/")),
        )
    if payload.auth_token:
        set_secret(f"model_source:{source_id}:auth_token", payload.auth_token)
    log_event("model.source.add", f"Added model source {payload.name}", {"source_id": source_id})
    return ModelSourceResponse(
        id=source_id,
        name=payload.name,
        base_url=payload.base_url.rstrip("/"),
        is_local=False,
        has_auth_token=bool(payload.auth_token),
    )


async def _fetch_models(source: ModelSourceResponse) -> list[str]:
    token = get_secret(f"model_source:{source.id}:auth_token")
    headers = {"Authorization": token} if token else {}
    url = f"{source.base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return [item["name"] for item in data.get("models", [])]
    except Exception:
        return []


async def list_model_options() -> list[ModelOptionResponse]:
    options: list[ModelOptionResponse] = []
    for source in list_model_sources():
        models = await _fetch_models(source)
        for model in models:
            options.append(
                ModelOptionResponse(
                    source_id=source.id,
                    source_name=source.name,
                    base_url=source.base_url,
                    model=model,
                )
            )
    return options


async def test_model_source(source_id: str) -> SourceTestResponse:
    source = next((s for s in list_model_sources() if s.id == source_id), None)
    if not source:
        return SourceTestResponse(ok=False, detail="Source not found")
    models = await _fetch_models(source)
    ok = len(models) > 0
    detail = f"Found {len(models)} model(s)" if ok else "Could not fetch models"
    log_event("model.source.test", detail, {"source_id": source_id, "ok": ok})
    return SourceTestResponse(ok=ok, detail=detail)


def get_source(source_id: str) -> ModelSourceResponse | None:
    return next((s for s in list_model_sources() if s.id == source_id), None)

