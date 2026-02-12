"""Local vector-like search using simple term frequency."""

from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from typing import Any

from app.db.sqlite import connection
from app.services.path_security import path_within_scopes
from app.services.workspaces import get_active_workspace


WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def _embed(text: str) -> dict[str, int]:
    tokens = [t.lower() for t in WORD_RE.findall(text)]
    return dict(Counter(tokens))


def _score(query_vec: dict[str, int], doc_vec: dict[str, int]) -> float:
    score = 0.0
    for key, qv in query_vec.items():
        score += qv * doc_vec.get(key, 0)
    return score


def index_documents(workspace_id: str, items: list[dict[str, Any]]) -> int:
    # items: [{path, content, content_hash}]
    with connection() as conn:
        for item in items:
            vec = _embed(item["content"])
            conn.execute(
                """
                INSERT INTO vector_index (id, workspace_id, path, content_hash, embedding_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), workspace_id, item["path"], item["content_hash"], json.dumps(vec)),
            )
    return len(items)


def search_index(workspace_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    qvec = _embed(query)
    with connection() as conn:
        rows = conn.execute(
            "SELECT path, embedding_json FROM vector_index WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchall()
    scored = []
    for row in rows:
        vec = json.loads(row["embedding_json"])
        scored.append((row["path"], _score(qvec, vec)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [{"path": p, "score": s} for p, s in scored[:limit]]


def can_index_path(path: str) -> bool:
    ws = get_active_workspace()
    if not ws or not ws.get("scopes"):
        return False
    return path_within_scopes(path, ws["scopes"])[0]
