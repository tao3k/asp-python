from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from snapshot_support import assert_snapshot, normalize_temp_root

from asp_python import (
    render_python_lang_harness,
    run_asp_python,
    run_python_lang_harness,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_py_agent_r001_module_intent_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        "def build(value: int) -> int:\n    return value\n", encoding="utf-8"
    )

    _assert_lang_snapshot(
        tmp_path,
        [source],
        "PY-AGENT-POLICY-001",
        "py_agent_r001_module_intent",
    )


def test_py_agent_r002_callable_annotations_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '"""Service helpers."""\n\n\ndef build(value):\n    return value\n',
        encoding="utf-8",
    )

    _assert_lang_snapshot(
        tmp_path,
        [source],
        "PY-AGENT-POLICY-002",
        "py_agent_r002_callable_annotations",
    )


def test_py_agent_r003_callable_conflict_snapshot(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "alpha.py").write_text(
        '"""Alpha namespace."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "beta.py").write_text(
        '"""Beta namespace."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-POLICY-003",
        "py_agent_r003_callable_conflict",
    )


def test_py_agent_r004_repeated_namespace_snapshot(tmp_path: Path) -> None:
    namespace = tmp_path / "src" / "domain" / "domain"
    namespace.mkdir(parents=True)
    (namespace / "service.py").write_text(
        '"""Domain service."""\n\nVALUE = 1\n', encoding="utf-8"
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-POLICY-004",
        "py_agent_r004_repeated_namespace",
    )


def test_py_agent_r005_type_conflict_snapshot(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "alpha.py").write_text(
        '"""Alpha namespace."""\n\n\nclass Service:\n    pass\n',
        encoding="utf-8",
    )
    (package / "beta.py").write_text(
        '"""Beta namespace."""\n\n\nclass Service:\n    pass\n',
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-POLICY-005",
        "py_agent_r005_type_conflict",
    )


def test_py_agent_r006_value_conflict_snapshot(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "alpha.py").write_text(
        '"""Alpha namespace."""\n\nDEFAULT_LIMIT = 1\n',
        encoding="utf-8",
    )
    (package / "beta.py").write_text(
        '"""Beta namespace."""\n\nDEFAULT_LIMIT = 2\n',
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-POLICY-006",
        "py_agent_r006_value_conflict",
    )


def test_py_agent_r007_branch_intent_snapshot(tmp_path: Path) -> None:
    branch = tmp_path / "src" / "pkg" / "domain"
    branch.mkdir(parents=True)
    (branch / "__init__.py").write_text("", encoding="utf-8")
    (branch / "service.py").write_text('"""Service leaf."""\n', encoding="utf-8")
    (branch / "models.py").write_text('"""Model leaf."""\n', encoding="utf-8")

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-POLICY-007",
        "py_agent_r007_branch_intent",
    )


def test_py_agent_r008_branch_surface_snapshot(tmp_path: Path) -> None:
    branch = tmp_path / "src" / "pkg" / "domain"
    branch.mkdir(parents=True)
    (branch / "__init__.py").write_text(
        '"""Domain package owner."""\n',
        encoding="utf-8",
    )
    for index in range(6):
        (branch / f"feature_{index}.py").write_text(
            f'"""Feature {index} owner."""\n\n\n'
            f"def build_{index}(value: int) -> int:\n"
            f"    return value + {index}\n",
            encoding="utf-8",
        )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-POLICY-008",
        "py_agent_r008_branch_surface",
    )


def _assert_lang_snapshot(
    root: Path,
    paths: list[Path],
    rule_id: str,
    snapshot_name: str,
) -> None:
    report = run_python_lang_harness(paths)
    _assert_filtered_snapshot(root, report, rule_id, snapshot_name)


def _assert_project_snapshot(
    root: Path,
    rule_id: str,
    snapshot_name: str,
) -> None:
    report = run_asp_python(root)
    _assert_filtered_snapshot(root, report, rule_id, snapshot_name)


def _assert_filtered_snapshot(
    root: Path,
    report,
    rule_id: str,
    snapshot_name: str,
) -> None:
    filtered = replace(
        report,
        findings=tuple(
            finding for finding in report.findings if finding.rule_id == rule_id
        ),
    )
    assert filtered.findings, f"expected at least one {rule_id} finding"
    rendered = normalize_temp_root(render_python_lang_harness(filtered), root)
    assert_snapshot(
        f"unit_test__agent_policy_snapshot__{snapshot_name}",
        rendered,
        source="tests/unit/harness/test_agent_policy_snapshots.py",
    )
