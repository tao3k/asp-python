"""Predicate matrix tests for Python tree-sitter-compatible query projection."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from asp_python import run_cli


def test_cli_query_inline_s_expression_applies_predicate_matrix(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    cases = [
        (
            "#eq?",
            "eq",
            [{"kind": "string", "value": "fetch"}],
            "src/pkg/service.py:9\nfetch\n",
        ),
        (
            "#any-eq?",
            "any-eq",
            [{"kind": "string", "value": "build"}],
            "src/pkg/service.py:12\nbuild\n",
        ),
        (
            "#any-of?",
            "any-of",
            [
                {"kind": "string", "value": "missing"},
                {"kind": "string", "value": "build"},
            ],
            "src/pkg/service.py:12\nbuild\n",
        ),
        (
            "#match?",
            "match",
            [{"kind": "string", "value": "^f"}],
            "src/pkg/service.py:9\nfetch\n",
        ),
        (
            "#any-match?",
            "any-match",
            [{"kind": "string", "value": "^b"}],
            "src/pkg/service.py:12\nbuild\n",
        ),
        (
            "#not-eq?",
            "not-eq",
            [{"kind": "string", "value": "fetch"}],
            "src/pkg/service.py:12\nbuild\n",
        ),
        (
            "#not-match?",
            "not-match",
            [{"kind": "string", "value": "^f"}],
            "src/pkg/service.py:12\nbuild\n",
        ),
        (
            "#eq?",
            "eq",
            [{"kind": "capture", "value": "function.name"}],
            "src/pkg/service.py:9\nfetch\n\nsrc/pkg/service.py:12\nbuild\n",
        ),
    ]
    for query_operator, plan_operator, values, expected in cases:
        stdout = io.StringIO()
        exit_code = run_cli(
            _function_name_query_args(
                _function_name_predicate_query(query_operator, values),
                tmp_path,
                _predicate_plan_args(plan_operator, values),
                "--selector",
                "src/pkg/service.py",
            ),
            stdout=stdout,
        )

        assert exit_code == 0
        assert stdout.getvalue() == expected


def test_cli_query_inline_s_expression_renders_multi_path_corpus_locators(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    (tmp_path / "src" / "pkg" / "extra.py").write_text(
        "def alpha() -> str:\n    return 'alpha'\n",
        encoding="utf-8",
    )
    stdout = io.StringIO()
    values = [
        {"kind": "string", "value": "alpha"},
        {"kind": "string", "value": "fetch"},
    ]

    exit_code = run_cli(
        _function_name_query_args(
            _function_name_predicate_query("#any-of?", values),
            tmp_path,
            _predicate_plan_args("any-of", values),
        ),
        stdout=stdout,
    )

    assert exit_code == 0
    assert stdout.getvalue() == (
        "src/pkg/extra.py:1\nalpha\n\nsrc/pkg/service.py:9\nfetch\n"
    )
    assert "|syntax-capture" not in stdout.getvalue()
    assert "artifactId" not in stdout.getvalue()


def _function_name_query_args(
    query: str,
    project_root: Path,
    plan_args: list[str],
    *extra_args: str,
) -> list[str]:
    return [
        "query",
        "--treesitter-query",
        query,
        *extra_args,
        "--workspace",
        str(project_root),
        "--asp-syntax-query-captures",
        "function.name",
        "--asp-syntax-query-node-types",
        "function_definition,identifier",
        "--asp-syntax-query-fields",
        "name",
        *plan_args,
    ]


def _function_name_predicate_query(
    query_operator: str,
    values: list[dict[str, str]],
) -> str:
    operands = " ".join(_predicate_query_operand(value) for value in values)
    return (
        "(function_definition name: (identifier) @function.name "
        f"({query_operator} @function.name {operands}))"
    )


def _predicate_query_operand(value: dict[str, str]) -> str:
    if value["kind"] == "capture":
        return f"@{value['value']}"
    return json.dumps(value["value"])


def _predicate_plan_args(op: str, values: list[dict[str, str]]) -> list[str]:
    return [
        "--asp-syntax-query-predicates-json",
        json.dumps(
            [
                {
                    "op": op,
                    "capture": "function.name",
                    "values": values,
                }
            ]
        ),
    ]
