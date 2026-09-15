"""Agent-readability symbol boundaries backed by parser role helpers."""

from __future__ import annotations

from pathlib import PurePath
from typing import TYPE_CHECKING

from python_lang_parser import (
    python_symbol_is_public_callable,
    python_symbol_is_public_callable_boundary,
    python_symbol_is_public_class,
    python_symbol_is_test_function,
)

if TYPE_CHECKING:
    from python_lang_parser import PythonModuleReport, PythonSymbol


def agent_readability_function_is_boundary(
    symbol: PythonSymbol,
    *,
    public_class_scopes: frozenset[str],
) -> bool:
    """Return whether a callable should receive agent-readability advice."""

    if python_symbol_is_test_function(symbol):
        return False
    return python_symbol_is_public_callable(symbol) or (
        python_symbol_is_public_callable_boundary(
            symbol,
            public_class_scopes=public_class_scopes,
        )
    )


def agent_readability_report_is_test(report: PythonModuleReport) -> bool:
    """Return whether a parser report belongs to a test module."""

    if report.path is None:
        return False
    path = PurePath(report.path.replace("\\", "/"))
    return "tests" in path.parts or path.name.startswith("test_")


def agent_readability_report_is_in_scope(report: PythonModuleReport) -> bool:
    """Return whether agent-readability advice should inspect this module."""

    return not agent_readability_report_is_test(report)


def agent_readability_public_class_scopes(
    report: PythonModuleReport,
) -> frozenset[str]:
    """Return parser-owned public class scopes for method boundary checks."""

    return frozenset(
        symbol.qualified_name
        for symbol in report.symbols
        if python_symbol_is_public_class(symbol)
    )
