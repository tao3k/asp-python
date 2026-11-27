"""Decorator and effect projection nodes for Python compact AST."""

from __future__ import annotations

import ast
from collections.abc import Iterable

from asp_python._python_expr import _expr
from asp_python._python_projection_model import (
    CompactPythonProjectionNode,
    python_ast_node_read,
)


def append_decorator_projection_nodes(
    nodes: list[CompactPythonProjectionNode],
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> None:
    for decorator in _python_decorator_nodes(node):
        nodes.append(
            CompactPythonProjectionNode(
                kind="decorator",
                role="declaration",
                label=f"@{_expr(decorator)}",
                depth=depth + 1,
                read=python_ast_node_read(owner_path, start_line, decorator),
                flags=("decorator",),
            )
        )


def append_expression_effect_projection_nodes(
    nodes: list[CompactPythonProjectionNode],
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> None:
    for effect_node in _python_expression_effect_nodes(node):
        nodes.append(
            CompactPythonProjectionNode(
                kind="await",
                role="effect",
                label=f"await {_expr(effect_node.value)}",
                depth=depth + 1,
                read=python_ast_node_read(owner_path, start_line, effect_node),
                flags=("await",),
            )
        )


def _python_decorator_nodes(node: ast.AST) -> tuple[ast.AST, ...]:
    decorator_list = getattr(node, "decorator_list", ())
    return tuple(
        decorator for decorator in decorator_list if isinstance(decorator, ast.AST)
    )


def _python_expression_effect_nodes(node: ast.AST) -> Iterable[ast.Await]:
    if not isinstance(node, ast.Expr | ast.Assign | ast.AnnAssign | ast.Return):
        return ()
    return tuple(child for child in ast.walk(node) if isinstance(child, ast.Await))
