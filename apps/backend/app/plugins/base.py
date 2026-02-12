"""Backend plugin contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class PermissionRequirement:
    permission: str
    path_scoped: bool = False


class ToolPlugin(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]
    permission_requirements: list[PermissionRequirement]

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...
