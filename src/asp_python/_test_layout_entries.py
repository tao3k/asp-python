"""Tests-root entry policy helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._model import AspPythonFinding
from ._source import path_location, source_line
from ._test_layout_catalog import (
    ALLOWED_TEST_DIR_NAMES,
    ALLOWED_TEST_ROOT_FILES,
    PY_TEST_R001,
    PY_TEST_R002,
    test_layout_rule,
)
from ._test_layout_config import load_test_layout_policy

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from python_lang_parser import PythonModuleReport


def tests_root_entry_findings(
    tests_dir: Path,
    pack_id: str,
    modules: Sequence[PythonModuleReport] = (),
) -> tuple[AspPythonFinding, ...]:
    """Return tests-root ownership findings for one test root."""

    policy = load_test_layout_policy(tests_dir)
    modules_by_path = _modules_by_path(modules)
    findings: list[AspPythonFinding] = []
    for path in sorted(tests_dir.iterdir(), key=lambda item: item.as_posix()):
        name = path.name
        if name.startswith("."):
            continue
        if path.is_dir():
            if name not in ALLOWED_TEST_DIR_NAMES and not policy.allows_directory(name):
                findings.append(
                    _unexpected_tests_root_entry_finding(path, pack_id, modules_by_path)
                )
            continue
        if (
            path.suffix != ".py"
            or name in ALLOWED_TEST_ROOT_FILES
            or policy.allows_root_file(name)
        ):
            continue
        if name.startswith("test_"):
            findings.append(_root_pytest_file_finding(path, pack_id, modules_by_path))
        else:
            findings.append(
                _unexpected_tests_root_entry_finding(path, pack_id, modules_by_path)
            )
    return tuple(findings)


def _root_pytest_file_finding(
    path: Path,
    pack_id: str,
    modules_by_path: Mapping[Path, PythonModuleReport],
) -> AspPythonFinding:
    rule = test_layout_rule(PY_TEST_R001)
    return AspPythonFinding(
        rule_id=rule.rule_id,
        pack_id=pack_id,
        severity=rule.severity,
        title=rule.title,
        summary=f"{path.name} is a pytest module directly under tests root.",
        location=path_location(path),
        requirement=rule.requirement,
        source_line=_entry_source_line(path, modules_by_path, 1),
        label="move this pytest module under tests/unit/ or tests/integration/",
        labels=dict(rule.labels),
    )


def _unexpected_tests_root_entry_finding(
    path: Path,
    pack_id: str,
    modules_by_path: Mapping[Path, PythonModuleReport],
) -> AspPythonFinding:
    rule = test_layout_rule(PY_TEST_R002)
    return AspPythonFinding(
        rule_id=rule.rule_id,
        pack_id=pack_id,
        severity=rule.severity,
        title=rule.title,
        summary=f"{path.name} is not an owned tests root entry.",
        location=path_location(path),
        requirement=rule.requirement,
        source_line=(
            _entry_source_line(path, modules_by_path, 1) if path.is_file() else None
        ),
        label="move this entry into an owned tests suite directory",
        labels=dict(rule.labels),
    )


def _entry_source_line(
    path: Path,
    modules_by_path: Mapping[Path, PythonModuleReport],
    line: int,
) -> str | None:
    """Return parser-captured source for Python files, with file fallback."""

    if path.suffix == ".py":
        report = modules_by_path.get(path.resolve())
        if report is not None:
            return report.source_line(line)
    return source_line(str(path), line)


def _modules_by_path(
    modules: Sequence[PythonModuleReport],
) -> dict[Path, PythonModuleReport]:
    return {
        Path(report.path).resolve(): report
        for report in modules
        if report.path is not None
    }
