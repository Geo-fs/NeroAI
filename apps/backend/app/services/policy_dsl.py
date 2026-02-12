"""Simple policy-as-code DSL parser and evaluator."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


Effect = Literal["allow", "deny"]


@dataclass(frozen=True)
class Condition:
    profile: str | None = None
    workspace: str | None = None
    require_confirm: bool = False


@dataclass(frozen=True)
class EffectRule:
    effect: Effect
    action: str
    condition: Condition


@dataclass(frozen=True)
class LimitRule:
    key: str
    value: int
    condition: Condition


@dataclass(frozen=True)
class PolicyParseResult:
    effects: list[EffectRule]
    limits: list[LimitRule]
    errors: list[str]


_ACTION_RE = re.compile(r"^(allow|deny)\(([^)]+)\)\s*(.*)$", re.IGNORECASE)
_LIMIT_RE = re.compile(r"^([a-zA-Z0-9_.]+)\s*=\s*([0-9]+)\s*(.*)$")


def _parse_condition(tail: str) -> Condition | None:
    tail = tail.strip()
    if not tail:
        return Condition()
    if tail.lower() == "always":
        return Condition()
    if tail.lower() == "unless confirm":
        return Condition(require_confirm=True)
    if tail.lower().startswith("only in "):
        tail = tail[8:].strip()
    if tail.lower().startswith("in "):
        tail = tail[3:].strip()
    if "=" in tail:
        parts = tail.split("=", 1)
        key = parts[0].strip().lower()
        value = parts[1].strip()
        if key == "profile":
            return Condition(profile=value)
        if key == "workspace":
            return Condition(workspace=value)
    return None


def parse_policy(text: str) -> PolicyParseResult:
    effects: list[EffectRule] = []
    limits: list[LimitRule] = []
    errors: list[str] = []
    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _ACTION_RE.match(line)
        if m:
            effect = m.group(1).lower()
            action = m.group(2).strip()
            tail = m.group(3).strip()
            cond = _parse_condition(tail)
            if cond is None:
                errors.append(f"Line {idx}: invalid condition '{tail}'")
                continue
            effects.append(EffectRule(effect=effect, action=action, condition=cond))
            continue
        m2 = _LIMIT_RE.match(line)
        if m2:
            key = m2.group(1).strip()
            value = int(m2.group(2))
            tail = m2.group(3).strip()
            cond = _parse_condition(tail)
            if cond is None:
                errors.append(f"Line {idx}: invalid condition '{tail}'")
                continue
            limits.append(LimitRule(key=key, value=value, condition=cond))
            continue
        errors.append(f"Line {idx}: unsupported rule syntax '{line}'")
    return PolicyParseResult(effects=effects, limits=limits, errors=errors)


def _condition_matches(cond: Condition, profile: str | None, workspace: str | None, confirmed: bool) -> bool:
    if cond.require_confirm and not confirmed:
        return False
    if cond.profile and (profile or "").lower() != cond.profile.lower():
        return False
    if cond.workspace and (workspace or "").lower() != cond.workspace.lower():
        return False
    return True


def evaluate_effect(
    rules: list[EffectRule],
    action: str,
    profile: str | None,
    workspace: str | None,
    confirmed: bool = False,
) -> Effect | None:
    decision: Effect | None = None
    for rule in rules:
        if rule.action.lower() != action.lower():
            continue
        if _condition_matches(rule.condition, profile, workspace, confirmed):
            if rule.effect == "deny":
                return "deny"
            decision = "allow"
    return decision


def apply_limit_overrides(
    base: dict[str, int],
    rules: list[LimitRule],
    profile: str | None,
    workspace: str | None,
    confirmed: bool = False,
) -> dict[str, int]:
    updated = dict(base)
    for rule in rules:
        if rule.key not in updated:
            continue
        if _condition_matches(rule.condition, profile, workspace, confirmed):
            updated[rule.key] = int(rule.value)
    return updated
