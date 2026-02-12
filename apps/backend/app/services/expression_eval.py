"""Safe boolean expression evaluation for workflow conditions."""

from __future__ import annotations

import ast
from typing import Any


ALLOWED_NODES = {
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Gt,
    ast.GtE,
    ast.Lt,
    ast.LtE,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Subscript,
    ast.Attribute,
}


def evaluate_condition(expression: str, context: dict[str, Any]) -> bool:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")
        if isinstance(node, ast.Call):
            raise ValueError("Function calls are not allowed")
    return bool(_eval_node(tree.body, context))


def _eval_node(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return context.get(node.id)
    if isinstance(node, ast.Attribute):
        base = _eval_node(node.value, context)
        if isinstance(base, dict):
            return base.get(node.attr)
        return getattr(base, node.attr, None)
    if isinstance(node, ast.Subscript):
        base = _eval_node(node.value, context)
        index = _eval_node(node.slice, context) if not isinstance(node.slice, ast.Constant) else node.slice.value
        if isinstance(base, dict):
            return base.get(index)
        if isinstance(base, (list, tuple)) and isinstance(index, int):
            return base[index]
        return None
    if isinstance(node, ast.BoolOp):
        vals = [_eval_node(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(vals)
        if isinstance(node.op, ast.Or):
            return any(vals)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not bool(_eval_node(node.operand, context))
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, context)
            ok = False
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            if not ok:
                return False
            left = right
        return True
    raise ValueError(f"Unsupported expression: {type(node).__name__}")

