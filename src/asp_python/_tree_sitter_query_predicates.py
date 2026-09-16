"""Typed predicate helpers for Python tree-sitter-compatible queries."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ._tree_sitter_query_model import SyntaxQueryRow


@dataclass(frozen=True)
class SyntaxQueryPredicateValue:
    kind: str
    value: str


@dataclass(frozen=True)
class SyntaxQueryPredicate:
    op: str
    capture: str
    values: tuple[SyntaxQueryPredicateValue, ...]


def syntax_predicates_match(
    row: SyntaxQueryRow,
    predicates: tuple[SyntaxQueryPredicate, ...],
) -> bool:
    return all(_syntax_predicate_match(row, predicate) for predicate in predicates)


def _syntax_predicate_match(
    row: SyntaxQueryRow,
    predicate: SyntaxQueryPredicate,
) -> bool:
    capture_text = _predicate_capture_text(row, predicate.capture)
    values = [_predicate_value_text(row, value) for value in predicate.values]
    match predicate.op:
        case "eq" | "any-eq" | "any-of":
            return any(capture_text == value for value in values)
        case "match" | "any-match":
            return any(re.search(value, capture_text) is not None for value in values)
        case "not-eq":
            return all(capture_text != value for value in values)
        case "not-match":
            return all(re.search(value, capture_text) is None for value in values)
        case _:
            raise ValueError(f"unsupported tree-sitter predicate op: {predicate.op}")


def _predicate_value_text(
    row: SyntaxQueryRow,
    value: SyntaxQueryPredicateValue,
) -> str:
    return (
        value.value
        if value.kind == "string"
        else _predicate_capture_text(row, value.value)
    )


def _predicate_capture_text(row: SyntaxQueryRow, capture: str) -> str:
    if capture == row.capture:
        return _syntax_capture_text(row)
    if (
        capture.endswith(".name")
        or capture.endswith(".target")
        or capture.endswith(".method")
        or capture.endswith(".source")
        or capture.endswith(".path")
        or capture.endswith(".alias")
        or capture.endswith(".keyword")
    ):
        return row.name
    if capture.endswith(".definition") or capture.endswith(".expression"):
        return row.item_code
    return _syntax_capture_text(row)


def _syntax_capture_text(row: SyntaxQueryRow) -> str:
    if (
        row.capture.endswith(".name")
        or row.capture.endswith(".target")
        or row.capture.endswith(".method")
        or row.capture.endswith(".source")
        or row.capture.endswith(".path")
        or row.capture.endswith(".alias")
        or row.capture.endswith(".keyword")
    ):
        return row.name
    if row.capture.endswith(".definition") or row.capture.endswith(".expression"):
        return row.item_code
    return next(
        (line.strip() for line in row.item_code.splitlines() if line.strip()),
        row.name,
    )
