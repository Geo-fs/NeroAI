"""Ollama client helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx


async def stream_ollama_chat(base_url: str, model: str, message: str, auth_token: str | None = None) -> AsyncGenerator[str, None]:
    headers = {"Authorization": auth_token} if auth_token else {}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "stream": True,
    }
    url = f"{base_url.rstrip('/')}/api/chat"
    async with httpx.AsyncClient(timeout=90) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = httpx.Response(200, content=line).json()
                except Exception:
                    continue
                msg = data.get("message", {}).get("content")
                if msg:
                    yield msg
