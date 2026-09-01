"""Unit-test leaf size policy helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser import python_symbol_is_test_function

from ._model import AspPythonFinding
from ._source import path_location
from ._test_layout_catalog import (
    MAX_UNIT_TEST_EFFECTIVE_LINES,
    MIN_UNIT_TEST_FUNCTIONS,
    PY_TEST_R003,
    test_layout_rule,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonModuleReport, PythonSymbol

    from ._model import PythonProjectHarnessScope


def bloated_unit_test_findings(
    scope: PythonProjectHarnessScope,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return oversized unit-test leaf findings from parser-owned facts."""

    unit_dirs = tuple(
        tests_dir / "unit"
        for tests_dir in scope.test_paths
        if (tests_dir / "unit").exists()
    )
    if not unit_dirs:
        return ()

    findings: list[AspPythonFinding] = []
    for report in sorted(modules, key=lambda item: item.path or ""):
        if report.path is None or not report.is_valid or report.shape is None:
            continue
        path = Path(report.path)
        if not _is_unit_test_module(path, unit_dirs):
            continue
        if path.name == "__init__.py":
            continue
        effective_code_lines = report.shape.effective_code_lines
        if effective_code_lines < MAX_UNIT_TEST_EFFECTIVE_LINES:
            continue
        test_functions = _count_parser_test_functions(report.symbols)
        if test_functions < MIN_UNIT_TEST_FUNCTIONS:
            continue
        findings.append(
            _bloated_unit_test_finding(
                path,
                pack_id,
                effective_code_lines=effective_code_lines,
                test_functions=test_functions,
                source_line=report.source_line(1),
            )
        )
    return tuple(findings)


def _is_unit_test_module(path: Path, unit_dirs: tuple[Path, ...]) -> bool:
    return any(_is_relative_to(path, unit_dir) for unit_dir in unit_dirs)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _bloated_unit_test_finding(
    path: Path,
    pack_id: str,
    *,
    effective_code_lines: int,
    test_functions: int,
    source_line: str | None,
) -> AspPythonFinding:
    rule = test_layout_rule(PY_TEST_R003)
    return AspPythonFinding(
        rule_id=rule.rule_id,
        pack_id=pack_id,
        severity=rule.severity,
        title=rule.title,
        summary=(
            f"{path.name} has {effective_code_lines} effective lines across "
            f"{test_functions} test functions."
        ),
        location=path_location(path),
        requirement=(
            f"Split {path.name} into a folder-first unit suite; "
            f"current size is {effective_code_lines} effective lines across "
            f"{test_functions} tests."
        ),
        source_line=source_line,
        label="split this large unit test leaf into focused pytest modules",
        labels=dict(rule.labels),
    )


def _count_parser_test_functions(symbols: Sequence[PythonSymbol]) -> int:
    return sum(1 for symbol in symbols if python_symbol_is_test_function(symbol))
