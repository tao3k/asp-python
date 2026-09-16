"""JSON row helpers for Python tree-sitter-compatible query packets."""

from __future__ import annotations

from typing import Any

from ._tree_sitter_query_model import (
    SyntaxQueryRow,
    syntax_line_locator,
    syntax_query_line_range,
)


def _syntax_query_matches_json(rows: list[SyntaxQueryRow]) -> list[dict[str, Any]]:
    return [
        _syntax_query_match_json(index, row) for index, row in enumerate(rows, start=1)
    ]


def _syntax_query_native_fact_refs(rows: list[SyntaxQueryRow]) -> list[str]:
    return sorted({_syntax_query_native_fact_ref(row) for row in rows})


def _syntax_query_match_json(index: int, row: SyntaxQueryRow) -> dict[str, Any]:
    native_fact_ref = _syntax_query_native_fact_ref(row)
    semantic_handle_ref = f"symbol:{row.name}"
    return {
        "id": f"match.{index}",
        "patternIndex": 0,
        "range": {
            "path": row.path,
            "lineRange": syntax_query_line_range(
                row.item_start_line, row.item_end_line
            ),
        },
        "captures": [
            _syntax_query_capture_json(index, row, native_fact_ref, semantic_handle_ref)
        ],
        "nativeFactRefs": [native_fact_ref],
        "semanticHandleRefs": [semantic_handle_ref],
        "fields": {
            "symbol": row.name,
            "read": syntax_line_locator(row.path, row.start_line, row.end_line),
            "itemRead": syntax_line_locator(
                row.path, row.item_start_line, row.item_end_line
            ),
            "nodeType": row.node,
            "captureCount": 1,
        },
    }


def _syntax_query_capture_json(
    index: int,
    row: SyntaxQueryRow,
    native_fact_ref: str,
    semantic_handle_ref: str,
) -> dict[str, Any]:
    return {
        "id": f"capture.{index}",
        "name": row.capture,
        "nodeType": row.capture_node,
        "field": row.capture_field,
        "named": True,
        "range": {
            "path": row.path,
            "lineRange": syntax_query_line_range(row.start_line, row.end_line),
        },
        "nativeFactRefs": [native_fact_ref],
        "semanticHandleRefs": [semantic_handle_ref],
        "fields": {
            "symbol": row.name,
            "read": syntax_line_locator(row.path, row.start_line, row.end_line),
            "itemRead": syntax_line_locator(
                row.path, row.item_start_line, row.item_end_line
            ),
            "sourceAuthority": "native-parser",
            "nativeNodeType": row.node,
            "semanticKind": _syntax_query_semantic_kind(row.node),
        },
    }


def _syntax_query_native_fact_ref(row: SyntaxQueryRow) -> str:
    return (
        f"python:ast:{row.path}:"
        f"{syntax_query_line_range(row.item_start_line, row.item_end_line)}:"
        f"{row.name}"
    )


def _syntax_query_semantic_kind(node: str) -> str:
    if node in {"function_definition", "class_definition"}:
        return node.removesuffix("_definition")
    if node in {"import_statement", "import_from_statement"}:
        return "import"
    if node in {"call", "keyword_argument"}:
        return "call"
    if node == "decorator":
        return "decorator"
    if node.endswith("_statement"):
        return "control-flow"
    return "item"
