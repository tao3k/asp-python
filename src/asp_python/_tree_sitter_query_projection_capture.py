"""Capture helpers for Python tree-sitter-compatible query projection."""

from __future__ import annotations

import ast


def first_capture(captures: tuple[str, ...], *preferred: str) -> str | None:
    for capture in preferred:
        if capture in captures:
            return capture
    return captures[0] if captures else None


def call_capture(captures: tuple[str, ...], node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        capture = first_capture(captures, "call.method", "call.target")
        if capture is not None:
            return capture
    return first_capture(captures, "call.target", "call.expression")


def decorator_capture(captures: tuple[str, ...], node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        capture = first_capture(captures, "decorator.call", "decorator.expression")
        if capture is not None:
            return capture
    return first_capture(captures, "decorator.expression", "decorator.target")


def call_capture_node(capture: str | None, node: ast.Call) -> ast.AST:
    if capture is None or capture.endswith(".expression"):
        return node
    return node.func


def capture_node_type(node_type: str, capture: str, node: ast.AST) -> str:
    if capture.endswith(".name"):
        return "identifier"
    if capture.endswith(".keyword"):
        return "identifier"
    if capture.startswith("call.") and capture.endswith((".target", ".method")):
        if isinstance(node, ast.Name):
            return "identifier"
        if isinstance(node, ast.Attribute):
            return "identifier" if capture.endswith(".method") else "attribute"
    return node_type


def capture_field(capture: str, fields: tuple[str, ...]) -> str:
    suffixes = {
        ".method": "attribute",
        ".target": "function" if capture.startswith("call.") else "target",
        ".name": "name",
        ".condition": "condition",
        ".iterable": "iterable",
        ".keyword": "keyword",
    }
    preferred = next(
        (field for suffix, field in suffixes.items() if capture.endswith(suffix)),
        "item",
    )
    return next((field for field in fields if field == preferred), preferred)
