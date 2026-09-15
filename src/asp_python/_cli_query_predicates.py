"""ASP-compiled tree-sitter query predicate parsing for CLI args."""

from __future__ import annotations

import json

from ._tree_sitter_query_predicates import (
    SyntaxQueryPredicate,
    SyntaxQueryPredicateValue,
)


def parse_asp_syntax_query_predicates(value: str) -> list[SyntaxQueryPredicate]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(error.msg) from error
    if not isinstance(parsed, list):
        raise ValueError("expected predicate array")
    return [
        _parse_asp_syntax_query_predicate(predicate, index)
        for index, predicate in enumerate(parsed)
    ]


def _parse_asp_syntax_query_predicate(
    value: object,
    index: int,
) -> SyntaxQueryPredicate:
    if not isinstance(value, dict):
        raise ValueError(f"predicate {index} must be an object")
    op = _syntax_predicate_op(value.get("op"), index)
    capture = _string_field(value.get("capture"), f"predicate {index}.capture")
    values = value.get("values")
    if not isinstance(values, list):
        raise ValueError(f"predicate {index}.values must be an array")
    operands = tuple(
        _parse_asp_syntax_query_predicate_value(operand, index, operand_index)
        for operand_index, operand in enumerate(values)
    )
    if op in {"match", "any-match", "not-match"} and any(
        operand.kind != "string" for operand in operands
    ):
        raise ValueError(f"predicate {index}.{op} requires string operands")
    return SyntaxQueryPredicate(op=op, capture=capture, values=operands)


def _parse_asp_syntax_query_predicate_value(
    value: object,
    predicate_index: int,
    operand_index: int,
) -> SyntaxQueryPredicateValue:
    if not isinstance(value, dict):
        raise ValueError(
            f"predicate {predicate_index}.values[{operand_index}] must be an object"
        )
    kind = _string_field(
        value.get("kind"),
        f"predicate {predicate_index}.values[{operand_index}].kind",
    )
    if kind not in {"string", "capture"}:
        raise ValueError(
            f"predicate {predicate_index}.values[{operand_index}].kind is unsupported"
        )
    return SyntaxQueryPredicateValue(
        kind=kind,
        value=_string_field(
            value.get("value"),
            f"predicate {predicate_index}.values[{operand_index}].value",
        ),
    )


def _syntax_predicate_op(value: object, index: int) -> str:
    op = _string_field(value, f"predicate {index}.op")
    if op in {
        "eq",
        "any-eq",
        "any-of",
        "match",
        "any-match",
        "not-eq",
        "not-match",
    }:
        return op
    raise ValueError(f"predicate {index}.op is unsupported")


def _string_field(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value
