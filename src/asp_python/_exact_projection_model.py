"""Define exact Python selector and projection value boundaries."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

REQUEST_SCHEMA_ID = "agent.semantic-protocols.provider-native-exact-request"
RESPONSE_SCHEMA_ID = "agent.semantic-protocols.provider-native-exact-projection"
SKELETON_SCHEMA_ID = "agent.semantic-protocols.callable-skeleton"
EXACT_SELECTOR_SCHEMA_ID = "asp.exact-structural-selector.v1"
CANONICAL_SELECTOR_SCHEMA_ID = "asp.canonical-item-selector.v1"


@dataclass(frozen=True)
class ExactSelector:
    requested: str
    root: str
    owner_path: str
    kind: str
    symbol: str
    scopes: tuple[tuple[str, str, str], ...]
    segment_kind: str | None
    segment_identity: str | None


@dataclass(frozen=True)
class ProjectionSegment:
    kind: str
    label: str
    ordinal: int
    byte_start: int
    byte_end: int


def parse_selector(selector: str) -> ExactSelector:
    language, separator, body = selector.partition("://")
    if separator != "://" or language != "python":
        raise ValueError("exact selector must use python://")
    owner_path, fragment_separator, fragment = body.partition("#")
    if fragment_separator != "#" or not owner_path:
        raise ValueError("exact selector must include owner and item fragment")
    root_fragment, segment_separator, descendant = fragment.partition("/segment/")
    parts = root_fragment.split("/")
    if len(parts) < 3 or parts[0] != "item" or not all(parts[:3]):
        raise ValueError("exact selector item fragment is invalid")
    scope_parts = parts[3:]
    scopes: list[tuple[str, str, str]] = []
    if len(scope_parts) % 4 != 0:
        raise ValueError("exact selector item scope is invalid")
    for offset in range(0, len(scope_parts), 4):
        scope = scope_parts[offset : offset + 4]
        if scope[0] != "scope" or not all(scope[1:]):
            raise ValueError("exact selector item scope is invalid")
        scopes.append((scope[1], scope[2], unquote(scope[3])))
    root = f"python://{owner_path}#{root_fragment}"
    segment_kind = None
    segment_identity = None
    if segment_separator:
        descendant_parts = descendant.split("/")
        if len(descendant_parts) != 2 or not all(descendant_parts):
            raise ValueError("exact descendant selector must be <kind>/<identity>")
        segment_kind, segment_identity = descendant_parts
    return ExactSelector(
        requested=selector,
        root=root,
        owner_path=owner_path,
        kind=parts[1],
        symbol=unquote(parts[2]),
        scopes=tuple(scopes),
        segment_kind=segment_kind,
        segment_identity=segment_identity,
    )


def find_function(
    tree: ast.AST, selector: ExactSelector
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if selector.kind not in {"function", "method"}:
        raise ValueError("callable projection requires function or method selector")
    search_root = tree
    for _role, owner_kind, owner_name in selector.scopes:
        if owner_kind != "type":
            raise ValueError("exact callable scope owner kind is unsupported")
        owners = [
            node
            for node in ast.iter_child_nodes(search_root)
            if isinstance(node, ast.ClassDef) and node.name == owner_name
        ]
        if len(owners) != 1:
            raise ValueError("exact callable scope owner is missing or ambiguous")
        search_root = owners[0]
    matches = [
        node
        for node in ast.walk(search_root)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == selector.symbol
    ]
    if len(matches) != 1:
        raise ValueError("exact callable selector is missing or ambiguous")
    return matches[0]


def line_byte_offsets(source: bytes) -> list[int]:
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def node_byte_span(node: ast.AST, line_offsets: list[int]) -> tuple[int, int]:
    lineno = getattr(node, "lineno", None)
    end_lineno = getattr(node, "end_lineno", None)
    if lineno is None or end_lineno is None:
        raise ValueError("Python AST node lacks exact source span")
    return (
        line_offsets[lineno - 1] + int(getattr(node, "col_offset", 0)),
        line_offsets[end_lineno - 1] + int(getattr(node, "end_col_offset", 0)),
    )


def flag_value(args: list[str] | tuple[str, ...], flag: str) -> str | None:
    for index, arg in enumerate(args):
        if arg == flag and index + 1 < len(args):
            return args[index + 1]
        prefix = f"{flag}="
        if arg.startswith(prefix):
            return arg[len(prefix) :]
    return None


def required_text(value: dict[str, Any], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise ValueError(f"exact request {field} must be non-empty text")
    return result


def required_int(value: dict[str, Any], field: str) -> int:
    result = value.get(field)
    if not isinstance(result, int) or result < 0:
        raise ValueError(f"exact request {field} must be a non-negative integer")
    return result
