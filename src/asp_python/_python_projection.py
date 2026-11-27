"""Collect compact projection nodes from Python AST statements."""

from __future__ import annotations

import ast

from asp_python._python_projection_extras import (
    append_decorator_projection_nodes,
    append_expression_effect_projection_nodes,
)
from asp_python._python_projection_facts import projection_fact
from asp_python._python_projection_model import (
    CompactPythonProjectionNode,
)


def collect_python_projection_node(
    nodes: list[CompactPythonProjectionNode],
    node: ast.AST,
    *,
    owner_path: str,
    start_line: int,
    depth: int,
    parent: ast.AST | None = None,
) -> None:
    fact = projection_fact(
        node, owner_path=owner_path, start_line=start_line, depth=depth, parent=parent
    )
    if fact is not None:
        nodes.append(fact)
        append_decorator_projection_nodes(nodes, node, owner_path, start_line, depth)
        append_expression_effect_projection_nodes(
            nodes, node, owner_path, start_line, depth
        )
    for child in ast.iter_child_nodes(node):
        if _is_projection_child(child):
            collect_python_projection_node(
                nodes,
                child,
                owner_path=owner_path,
                start_line=start_line,
                depth=depth + 1,
                parent=node,
            )


def _is_projection_child(node: ast.AST) -> bool:
    return isinstance(node, ast.stmt | ast.ExceptHandler | ast.match_case)
