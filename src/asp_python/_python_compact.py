"""Native AST compact projection for Python semantic query items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asp_python._python_outline import (
    fallback_python_compact,
)
from asp_python._python_projection import (
    CompactPythonProjectionNode,
    collect_python_projection_node,
)
from asp_python._python_source import parse_python_lines


@dataclass(frozen=True)
class CompactPythonItem:
    """Compact code and parser-owned projection nodes for one Python item."""

    code: str
    projection_nodes: list[dict[str, Any]]


def render_python_projection_outline(
    nodes: list[CompactPythonProjectionNode],
) -> str:
    """Render compact code from parser-owned projection labels."""

    return "\n".join(
        f"{'  ' * node.depth}{node.label}".rstrip()
        for node in nodes
        if node.label.strip()
    )


def compact_python_item(
    raw_lines: list[str],
    owner_path: str,
    start_line: int,
) -> CompactPythonItem:
    """Return AST-owned compact code and projection nodes for source lines."""

    tree = parse_python_lines(raw_lines)
    if tree is None:
        return CompactPythonItem(
            code=fallback_python_compact(raw_lines),
            projection_nodes=[],
        )
    projection_nodes: list[CompactPythonProjectionNode] = []
    for node in tree.body:
        collect_python_projection_node(
            projection_nodes,
            node,
            owner_path=owner_path,
            start_line=start_line,
            depth=0,
        )
    return CompactPythonItem(
        code=render_python_projection_outline(projection_nodes)
        or fallback_python_compact(raw_lines),
        projection_nodes=[node.as_packet_node() for node in projection_nodes[:80]],
    )
