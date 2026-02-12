"""FastAPI application entrypoint for NeroAI backend."""

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.sqlite import initialize_db
from app.services.ollama_status import refresh_ollama_status
from app.services.seed import seed_defaults
from app.services.settings_service import get_effective_settings


app = FastAPI(title="NeroAI Backend", version="0.1.0")
app.include_router(router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ollama_task: asyncio.Task | None = None


async def _ollama_poll_loop() -> None:
    while True:
        try:
            await refresh_ollama_status()
        except Exception:
            pass
        interval = max(5, int(get_effective_settings().ollama_check_interval_seconds))
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup() -> None:
    initialize_db()
    seed_defaults()
    await refresh_ollama_status()
    global _ollama_task
    _ollama_task = asyncio.create_task(_ollama_poll_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    global _ollama_task
    if _ollama_task:
        _ollama_task.cancel()
        try:
            await _ollama_task
        except asyncio.CancelledError:
            pass
        _ollama_task = None
