"""Typed packet nodes for Python compact AST projection."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Literal

_PythonCompactRole = Literal[
    "declaration",
    "field",
    "mutation",
    "control-flow",
    "call",
    "effect",
    "delimiter",
    "terminal",
]


@dataclass(frozen=True)
class CompactPythonProjectionNode:
    """Typed AST projection node before packet serialization."""

    kind: str
    role: _PythonCompactRole
    label: str
    depth: int
    read: str
    flags: tuple[str, ...] = ()

    def as_packet_node(self) -> dict[str, Any]:
        """Serialize the typed compact node for the shared query packet."""

        node: dict[str, Any] = {
            "kind": self.kind,
            "role": self.role,
            "label": self.label,
            "depth": self.depth,
            "read": self.read,
        }
        if self.flags:
            node["flags"] = list(self.flags)
        return node


def node_fact(
    node: ast.AST,
    kind: str,
    role: _PythonCompactRole,
    label: str,
    depth: int,
    owner_path: str,
    start_line: int,
    *,
    flags: tuple[str, ...] = (),
) -> CompactPythonProjectionNode:
    return CompactPythonProjectionNode(
        kind=kind,
        role=role,
        label=label,
        depth=depth,
        read=python_ast_node_read(owner_path, start_line, node),
        flags=flags,
    )


def python_ast_node_read(owner_path: str, start_line: int, node: ast.AST) -> str:
    line, end_line = _python_ast_node_span(node)
    absolute_start = start_line + line - 1
    absolute_end = start_line + end_line - 1
    return f"{owner_path}:{absolute_start}:{absolute_end}"


def _python_ast_node_span(node: ast.AST) -> tuple[int, int]:
    line = getattr(node, "lineno", None)
    if isinstance(line, int):
        end_line = getattr(node, "end_lineno", line) or line
        return line, int(end_line)

    child_spans = [
        _python_ast_node_span(child)
        for child in ast.iter_child_nodes(node)
        if _has_line_span(child)
    ]
    if not child_spans:
        return 1, 1
    return min(span[0] for span in child_spans), max(span[1] for span in child_spans)


def _has_line_span(node: ast.AST) -> bool:
    if isinstance(getattr(node, "lineno", None), int):
        return True
    return any(_has_line_span(child) for child in ast.iter_child_nodes(node))
