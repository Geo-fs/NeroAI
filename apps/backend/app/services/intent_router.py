"""Intent router with lightweight heuristics."""

from __future__ import annotations


def classify_intent(text: str) -> str:
    lower = text.lower()
    if "search" in lower or "look up" in lower:
        return "search.answer"
    if "summarize" in lower:
        return "summarize.docs"
    if "workflow" in lower or "run" in lower:
        return "workflow.run"
    if "code" in lower or "bug" in lower:
        return "code.help"
    if "file" in lower or "read" in lower or "write" in lower:
        return "file.ops"
    return "chat.general"
