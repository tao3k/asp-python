"""Native Python stdlib `ast` inspection (`ast-inspect`) and batched compiler
oracle verification (`ast-verify`) for ASP's `agent-semantic-ast` protocol."""

from __future__ import annotations

import ast
from typing import Any


def _line_utf8_offsets(source: str) -> list[int]:
    """Return 1-indexed UTF-8 byte start offsets for every line in `source`."""
    offsets = [0, 0]
    pos = 0
    for line in source.splitlines(keepends=True):
        pos += len(line.encode("utf-8"))
        offsets.append(pos)
    return offsets


def _byte_offset(offsets: list[int], lineno: int | None, col_offset: int | None) -> int:
    if lineno is None or lineno < 1:
        return 0
    idx = min(lineno, len(offsets) - 1)
    base = offsets[idx]
    col = max(col_offset or 0, 0)
    return base + col


def _node_span(offsets: list[int], node: ast.AST) -> dict[str, int]:
    start = _byte_offset(
        offsets, getattr(node, "lineno", None), getattr(node, "col_offset", None)
    )
    end = _byte_offset(
        offsets,
        getattr(node, "end_lineno", None),
        getattr(node, "end_col_offset", None),
    )
    return {"start": start, "end": max(end, start)}


def _outer_span(offsets: list[int], node: ast.AST) -> dict[str, int]:
    inner = _node_span(offsets, node)
    decorators = getattr(node, "decorator_list", None)
    if decorators:
        first_dec = _node_span(offsets, decorators[0])
        # Decorator AST node starts after `@`; step back over `@` if present.
        start = max(0, first_dec["start"] - 1)
        return {"start": min(start, inner["start"]), "end": inner["end"]}
    return inner


def _collect_nodes(
    path: str,
    offsets: list[int],
    stmts: list[ast.stmt],
    parent: str | None,
    out: list[dict[str, Any]],
) -> None:
    for stmt in stmts:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tag = "method" if parent else "fn"
            kind = "method" if parent else "function"
            lang_kind = (
                "async_function_def"
                if isinstance(stmt, ast.AsyncFunctionDef)
                else "function_def"
            )
            locator = (
                f"{parent}#{tag}:{stmt.name}" if parent else f"{path}#{tag}:{stmt.name}"
            )
            inner = _node_span(offsets, stmt)
            outer = _outer_span(offsets, stmt)
            body_span = None
            if stmt.body:
                b_start = _node_span(offsets, stmt.body[0])["start"]
                body_span = {"start": b_start, "end": inner["end"]}
            attrs: list[dict[str, str]] = []
            if isinstance(stmt, ast.AsyncFunctionDef):
                attrs.append({"key": "async", "value": "true"})
            out.append(
                {
                    "locator": locator,
                    "kind": kind,
                    "languageKind": lang_kind,
                    "name": stmt.name,
                    "line": stmt.lineno,
                    "outerSpan": outer,
                    "innerSpan": inner,
                    "bodySpan": body_span,
                    "parent": parent,
                    "attrs": attrs,
                }
            )
        elif isinstance(stmt, ast.ClassDef):
            locator = (
                f"{parent}#class:{stmt.name}" if parent else f"{path}#class:{stmt.name}"
            )
            inner = _node_span(offsets, stmt)
            outer = _outer_span(offsets, stmt)
            body_span = None
            if stmt.body:
                b_start = _node_span(offsets, stmt.body[0])["start"]
                body_span = {"start": b_start, "end": inner["end"]}
            out.append(
                {
                    "locator": locator,
                    "kind": "struct",
                    "languageKind": "class_def",
                    "name": stmt.name,
                    "line": stmt.lineno,
                    "outerSpan": outer,
                    "innerSpan": inner,
                    "bodySpan": body_span,
                    "parent": parent,
                    "attrs": [],
                }
            )
            _collect_nodes(path, offsets, stmt.body, locator, out)
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            span = _node_span(offsets, stmt)
            label = f"import_line_{stmt.lineno}"
            locator = f"{parent}#import:{label}" if parent else f"{path}#import:{label}"
            out.append(
                {
                    "locator": locator,
                    "kind": "import",
                    "languageKind": "import_from"
                    if isinstance(stmt, ast.ImportFrom)
                    else "import",
                    "name": label,
                    "line": stmt.lineno,
                    "outerSpan": span,
                    "innerSpan": span,
                    "bodySpan": None,
                    "parent": parent,
                    "attrs": [],
                }
            )


def _syntax_error_diagnostic(source: str, error: SyntaxError) -> dict[str, Any]:
    offsets = _line_utf8_offsets(source)
    col = (error.offset - 1) if error.offset and error.offset > 0 else 0
    byte_start = _byte_offset(offsets, error.lineno, col)
    end_col = (
        (error.end_offset - 1) if error.end_offset and error.end_offset > 0 else col
    )
    byte_end = max(
        byte_start, _byte_offset(offsets, error.end_lineno or error.lineno, end_col)
    )
    msg = error.msg or str(error)
    expected: list[str] = []
    for tok in (")", "]", "}", ":"):
        if f"'{tok}'" in msg or f'"{tok}"' in msg or "was never closed" in msg:
            if tok not in expected and (tok != ":" or "':'" in msg):
                expected.append(tok)
    return {
        "byteStart": byte_start,
        "byteEnd": byte_end,
        "message": msg,
        "expectedTokens": expected,
    }


PYTHON_SYNTAX_SURFACE: dict[str, Any] = {
    "lineComment": "#",
    "blockComment": None,
    "delimiterPairs": [["(", ")"], ["[", "]"], ["{", "}"]],
    "statementTerminator": None,
    "stringDelimiters": ['"', "'"],
}


def handle_ast_inspect(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse Python source with stdlib `ast` and emit authoritative UTF-8 spans."""
    path = str(payload.get("path", "<memory>"))
    source = str(payload.get("sourceUtf8", ""))
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as error:
        return {
            "accepted": False,
            "nodes": [],
            "diagnostics": [_syntax_error_diagnostic(source, error)],
            "syntaxSurface": PYTHON_SYNTAX_SURFACE,
        }
    offsets = _line_utf8_offsets(source)
    nodes: list[dict[str, Any]] = []
    _collect_nodes(path, offsets, tree.body, None, nodes)
    return {
        "accepted": True,
        "nodes": nodes,
        "diagnostics": [],
        "syntaxSurface": PYTHON_SYNTAX_SURFACE,
    }


def handle_ast_verify(payload: dict[str, Any]) -> dict[str, Any]:
    """Batch-verify candidate Python source buffers against stdlib `ast.parse`."""
    path = str(payload.get("path", "<memory>"))
    candidates = payload.get("candidates", [])
    results: list[dict[str, Any]] = []
    for cand in candidates:
        cand_id = str(cand.get("candidateId", ""))
        source = str(cand.get("sourceUtf8", ""))
        try:
            ast.parse(source, filename=path)
            results.append(
                {"candidateId": cand_id, "accepted": True, "diagnostics": []}
            )
        except SyntaxError as error:
            results.append(
                {
                    "candidateId": cand_id,
                    "accepted": False,
                    "diagnostics": [_syntax_error_diagnostic(source, error)],
                }
            )
    return {"results": results}
