from __future__ import annotations

import ast
import json
from typing import Any

from ._exact_projection_model import (
    CANONICAL_SELECTOR_SCHEMA_ID,
    EXACT_SELECTOR_SCHEMA_ID,
    SKELETON_SCHEMA_ID,
    ExactSelector,
    ProjectionSegment,
    node_byte_span,
    required_text,
)


def collect_segments(
    function: ast.FunctionDef | ast.AsyncFunctionDef, line_offsets: list[int]
) -> list[ProjectionSegment]:
    segments: list[ProjectionSegment] = []

    class Collector(ast.NodeVisitor):
        def _push(self, node: ast.AST, kind: str, label: str) -> None:
            start, end = node_byte_span(node, line_offsets)
            segments.append(
                ProjectionSegment(
                    kind=kind,
                    label=label,
                    ordinal=len(segments) + 1,
                    byte_start=start,
                    byte_end=end,
                )
            )

        def visit_Assign(self, node: ast.Assign) -> None:
            self._push(node, "binding", "assign")
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            self._push(node, "binding", "assign")
            self.generic_visit(node)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            self._push(node, "binding", "assign")
            self.generic_visit(node)

        def visit_If(self, node: ast.If) -> None:
            self._push(node, "branch", "if")
            self.generic_visit(node)

        def visit_Match(self, node: ast.Match) -> None:
            self._push(node, "branch", "match")
            self.generic_visit(node)

        def visit_For(self, node: ast.For) -> None:
            self._push(node, "loop", "for")
            self.generic_visit(node)

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
            self._push(node, "loop", "async-for")
            self.generic_visit(node)

        def visit_While(self, node: ast.While) -> None:
            self._push(node, "loop", "while")
            self.generic_visit(node)

        def visit_Return(self, node: ast.Return) -> None:
            self._push(node, "exit", "return")
            self.generic_visit(node)

        def visit_Raise(self, node: ast.Raise) -> None:
            self._push(node, "exit", "raise")
            self.generic_visit(node)

    collector = Collector()
    for statement in function.body:
        collector.visit(statement)
    return segments


def callable_skeleton_payload(
    request: dict[str, Any],
    selector: ExactSelector,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    segments: list[ProjectionSegment],
    root_start: int,
    root_end: int,
) -> dict[str, Any]:
    root_exact = exact_selector(request, selector, None)
    nodes: list[dict[str, Any]] = [
        {
            "nodeId": "callable:root",
            "kind": "callable",
            "label": function.name,
            "order": 0,
            "queryable": True,
            "exactSelector": root_exact,
            "languageFacts": {
                "async": isinstance(function, ast.AsyncFunctionDef),
                "decoratorCount": len(function.decorator_list),
                "inputCount": len(function.args.args)
                + len(function.args.posonlyargs)
                + len(function.args.kwonlyargs),
            },
        }
    ]
    relations: list[dict[str, str]] = []
    for segment in segments:
        node_id = f"{segment.kind}:{segment.ordinal}"
        nodes.append(
            {
                "nodeId": node_id,
                "kind": segment.kind,
                "label": segment.label,
                "order": segment.ordinal,
                "queryable": True,
                "exactSelector": exact_selector(request, selector, segment),
                "sourceLocatorHint": {
                    "sourceByteStart": segment.byte_start,
                    "sourceByteEnd": segment.byte_end,
                },
            }
        )
        relations.append(
            {
                "fromNodeId": "callable:root",
                "toNodeId": node_id,
                "kind": "contains",
            }
        )
    source_bytes = root_end - root_start
    structural_bytes = len(
        json.dumps(
            {"nodes": nodes, "relations": relations},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    projected_bytes = min(source_bytes, structural_bytes)
    return {
        "schemaId": SKELETON_SCHEMA_ID,
        "schemaVersion": "1",
        "projectionKind": "callable-skeleton",
        "languageId": "python",
        "providerId": "py-harness",
        "rootSelector": root_exact,
        "rootNodeId": "callable:root",
        "callable": {
            "kind": selector.kind,
            "displayName": function.name,
            "signature": function.name,
        },
        "nodes": nodes,
        "relations": relations,
        "cost": {
            "sourceBytes": source_bytes,
            "projectedBytes": projected_bytes,
            "omittedBytes": source_bytes - projected_bytes,
        },
        "languageFacts": {"parser": "ast", "syntax": "python"},
    }


def exact_selector(
    request: dict[str, Any],
    selector: ExactSelector,
    segment: ProjectionSegment | None,
) -> dict[str, Any]:
    segments: list[dict[str, str]] = []
    structural_selector = selector.root
    if segment is not None:
        identity = f"ordinal-{segment.ordinal}"
        segments.append(
            {
                "relation": "contains",
                "kind": segment.kind,
                "identity": identity,
                "label": segment.label,
            }
        )
        structural_selector = f"{selector.root}/segment/{segment.kind}/{identity}"
    return {
        "schemaId": EXACT_SELECTOR_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": "python",
        "ownerPath": selector.owner_path,
        "selector": structural_selector,
        "generationIdentityDigest": required_text(request, "generationIdentityDigest"),
        "parserIdentityDigest": required_text(request, "parserIdentityDigest"),
        "queryPackDigest": required_text(request, "queryPackDigest"),
        "rootItemSelector": {
            "schemaId": CANONICAL_SELECTOR_SCHEMA_ID,
            "schemaVersion": "1",
            "languageId": "python",
            "kind": selector.kind,
            "symbol": selector.symbol,
            "scopes": [],
            "structuralSelector": selector.root,
        },
        "segments": segments,
    }
