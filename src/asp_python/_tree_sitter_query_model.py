"""Shared model helpers for Python tree-sitter-compatible queries."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonTreeSitterCatalog:
    id: str
    path: str
    captures: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class SyntaxQuerySelector:
    path: str
    start_line: int | None = None
    end_line: int | None = None

    def display(self) -> str:
        if self.start_line is None or self.end_line is None:
            return self.path
        return f"{self.path}:{self.start_line}:{self.end_line}"


@dataclass(frozen=True)
class SyntaxQueryRow:
    capture: str
    capture_node: str
    capture_field: str
    node: str
    name: str
    path: str
    start_line: int
    end_line: int
    item_start_line: int
    item_end_line: int
    item_code: str


@dataclass(frozen=True)
class SyntaxQueryProjection:
    rows: list[SyntaxQueryRow]
    total_matches: int
    truncated: bool
    unsupported_nodes: list[str]

    def match_status(self) -> str:
        if self.unsupported_nodes and self.total_matches == 0:
            return "unsupported"
        return "hit" if self.total_matches else "miss"


MAX_SYNTAX_QUERY_ROWS = 80
SUPPORTED_TREE_SITTER_QUERY_NODES = frozenset(
    {
        "call",
        "class_definition",
        "decorated_definition",
        "decorator",
        "for_statement",
        "function_definition",
        "if_statement",
        "import_from_statement",
        "import_statement",
        "keyword_argument",
        "match_statement",
        "try_statement",
        "while_statement",
        "with_statement",
    }
)
LEAF_TREE_SITTER_QUERY_NODES = frozenset(
    {
        "_",
        "argument_list",
        "attribute",
        "block",
        "dotted_name",
        "identifier",
        "with_item",
    }
)


def capture_names(query_source: str) -> list[str]:
    captures: list[str] = []
    seen: set[str] = set()
    for capture in re.findall(r"@([A-Za-z][A-Za-z0-9_.-]*)", query_source):
        if capture in seen:
            continue
        seen.add(capture)
        captures.append(capture)
    return captures


def tree_sitter_query_nodes(query_source: str) -> frozenset[str]:
    return frozenset(
        token
        for token in re.findall(r"\(([A-Za-z_][A-Za-z0-9_]*)", query_source)
        if not token.startswith("#")
    )


def parse_selector(selector: str | None) -> SyntaxQuerySelector | None:
    if selector is None:
        return None
    normalized = selector.replace("\\", "/").removeprefix("owner:")
    if any(marker in normalized for marker in ("*", "{", "}")):
        raise ValueError("tree-sitter query selector must be an exact owner path")
    path_and_start, separator, end_text = normalized.rpartition(":")
    if not separator:
        return SyntaxQuerySelector(path=normalized)
    path, separator, start_text = path_and_start.rpartition(":")
    if not separator:
        start_text, separator, end_text = end_text.partition("-")
        if not separator:
            return SyntaxQuerySelector(path=normalized)
        path = path_and_start
    try:
        start_line = int(start_text)
        end_line = int(end_text)
    except ValueError:
        return SyntaxQuerySelector(path=normalized)
    return SyntaxQuerySelector(
        path=path,
        start_line=min(start_line, end_line),
        end_line=max(start_line, end_line),
    )


def selector_matches(row: SyntaxQueryRow, selector: SyntaxQuerySelector | None) -> bool:
    if selector is None:
        return True
    if not selector_path_matches(selector.path, row.path):
        return False
    if selector.start_line is None or selector.end_line is None:
        return True
    return (
        row.end_line >= selector.start_line and row.start_line <= selector.end_line
    ) or (
        row.item_end_line >= selector.start_line
        and row.item_start_line <= selector.end_line
    )


def selector_path_matches(selector_path: str, row_path: str) -> bool:
    normalized = selector_path.replace("\\", "/").removeprefix("./")
    row_normalized = row_path.replace("\\", "/").removeprefix("./")
    return normalized == row_normalized


def terms_match(row: SyntaxQueryRow, terms: list[str]) -> bool:
    if not terms:
        return True
    haystack = "\n".join((row.name, row.capture, row.node, row.item_code)).casefold()
    return any(term.casefold() in haystack for term in terms)


def node_span(node: ast.AST) -> tuple[int, int]:
    line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", line)
    if not isinstance(line, int):
        line = 1
    if not isinstance(end_line, int):
        end_line = line
    return max(1, line), max(max(1, line), end_line)


def syntax_line_locator(path: str, start_line: int, end_line: int) -> str:
    return f"{path}:{syntax_query_line_range(start_line, end_line)}"


def syntax_query_line_range(start_line: int, end_line: int) -> str:
    start = max(1, start_line)
    end = max(start, end_line)
    return str(start) if start == end else f"{start}:{end}"


def compact_value(value: str) -> str:
    if re.search(r"[\s,=]", value):
        return json.dumps(value)
    return value


def fingerprint(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
