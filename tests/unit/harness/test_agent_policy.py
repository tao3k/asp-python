from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from asp_python import (
    PythonAgentPolicyRulePack,
    python_agent_policy_rules,
    render_python_lang_harness,
    render_python_lang_harness_advice,
    run_asp_python,
    run_python_lang_harness,
)
from python_lang_parser import PythonDiagnosticSeverity

if TYPE_CHECKING:
    from pathlib import Path


def test_agent_policy_reports_compact_repairable_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text("def build(value):\n    return value\n", encoding="utf-8")

    report = run_python_lang_harness([source])
    output = render_python_lang_harness_advice(report)
    output = output.replace(str(source), "$TMP/service.py")

    assert report.is_clean
    rendered = render_python_lang_harness(report)
    assert rendered.startswith("[advice]\n[PY-AGENT-POLICY-001]")
    assert "[ok]" not in rendered
    assert (
        output
        == """[PY-AGENT-POLICY-001] Info: Library module lacks a module intent docstring
  --> $TMP/service.py:1:1
   1 | def build(value):
     | `- add a concise module responsibility docstring
     | Required: Add a concise module docstring that names the module responsibility for agent search and repair.

[PY-AGENT-POLICY-002] Info: Public callable lacks type annotations
  --> $TMP/service.py:1:1
   1 | def build(value):
     | `- add parameter and return annotations to this public callable
     | Required: Annotate public function and method boundaries so agents can reason from native syntax without guessing shapes.
"""
    )


def test_agent_policy_accepts_documented_annotated_public_callable(
    tmp_path: Path,
) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '"""Service helpers for tests."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])

    assert report.is_clean
    assert render_python_lang_harness_advice(report) == ""


def test_agent_policy_skips_test_modules(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    source = tests / "test_service.py"
    source.write_text("def test_value():\n    assert True\n", encoding="utf-8")

    report = run_python_lang_harness([tmp_path])

    assert report.is_clean


def test_agent_policy_blocks_duplicate_public_callable_names(
    tmp_path: Path,
) -> None:
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

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-POLICY-003", str(package / "beta.py")),
    ]
    assert "unambiguous names" in report.findings[0].requirement
    assert "namespace this public callable" in report.findings[0].label


def test_agent_policy_blocks_duplicate_public_type_names(
    tmp_path: Path,
) -> None:
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

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-POLICY-005", str(package / "beta.py")),
    ]
    assert "unambiguous type names" in report.findings[0].requirement
    assert "namespace this public type" in report.findings[0].label


def test_agent_policy_blocks_duplicate_public_value_names(
    tmp_path: Path,
) -> None:
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

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-POLICY-006", str(package / "beta.py")),
    ]
    assert "configuration exports" in report.findings[0].requirement
    assert "namespace this public value" in report.findings[0].label


def test_agent_policy_blocks_repeated_module_namespace_segments(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "src" / "domain" / "domain"
    namespace.mkdir(parents=True)
    source = namespace / "service.py"
    source.write_text(
        '"""Domain service namespace."""\n\nVALUE = 1\n', encoding="utf-8"
    )

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-POLICY-004", str(source)),
    ]
    assert "branch-unique" in report.findings[0].requirement
    assert "rename one repeated namespace segment" in report.findings[0].label


def test_agent_policy_deduplicates_repeated_namespace_branches(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "src" / "domain" / "domain"
    namespace.mkdir(parents=True)
    (namespace / "alpha.py").write_text('"""Alpha."""\n\nVALUE = 1\n', encoding="utf-8")
    (namespace / "beta.py").write_text(
        '"""Beta."""\n\nOTHER_VALUE = 2\n',
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert [finding.rule_id for finding in report.findings] == ["PY-AGENT-POLICY-004"]


def test_agent_policy_reports_broad_branch_package_surface(tmp_path: Path) -> None:
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

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-POLICY-008", str(branch / "__init__.py")),
    ]
    assert "one folder as one responsibility" in report.findings[0].requirement
    assert "owner map" in report.findings[0].label


def test_agent_policy_accepts_owner_map_documented_branch_package(
    tmp_path: Path,
) -> None:
    branch = tmp_path / "src" / "pkg" / "domain"
    branch.mkdir(parents=True)
    (branch / "__init__.py").write_text(
        '"""Domain package owner.\n\n'
        "Owner map:\n"
        "- feature_0 through feature_5 own individual domain behaviors.\n"
        '"""\n',
        encoding="utf-8",
    )
    for index in range(6):
        (branch / f"feature_{index}.py").write_text(
            f'"""Feature {index} owner."""\n\n\n'
            f"def build_{index}(value: int) -> int:\n"
            f"    return value + {index}\n",
            encoding="utf-8",
        )

    report = run_asp_python(tmp_path)

    assert not report.findings


def test_agent_policy_advice_can_be_promoted_to_blocking(
    tmp_path: Path,
) -> None:
    source = tmp_path / "service.py"
    source.write_text("def build(value):\n    return value\n", encoding="utf-8")

    report = run_python_lang_harness([source])

    assert report.is_clean
    assert [finding.rule_id for finding in report.advisory_findings()] == [
        "PY-AGENT-POLICY-001",
        "PY-AGENT-POLICY-002",
    ]
    assert [finding.rule_id for finding in report.blocking_findings()] == []
    assert [
        finding.rule_id
        for finding in report.blocking_findings(
            severities=frozenset({PythonDiagnosticSeverity.INFO})
        )
    ] == [
        "PY-AGENT-POLICY-001",
        "PY-AGENT-POLICY-002",
    ]
    promoted = replace(report, blocking_rule_ids=frozenset({"PY-AGENT-POLICY-001"}))
    advice = render_python_lang_harness_advice(promoted)

    assert "[PY-AGENT-POLICY-001]" not in advice
    assert advice.startswith("[PY-AGENT-POLICY-002]")


def test_agent_policy_descriptor_and_catalog_are_stable() -> None:
    descriptor = PythonAgentPolicyRulePack().descriptor()
    rules = python_agent_policy_rules()

    assert descriptor.id == "python.agent_policy"
    assert descriptor.to_dict()["domains"] == [
        "agent-policy",
        "project-shape",
        "python",
    ]
    assert [rule.rule_id for rule in rules] == [
        "PY-AGENT-POLICY-001",
        "PY-AGENT-POLICY-002",
        "PY-AGENT-POLICY-003",
        "PY-AGENT-POLICY-004",
        "PY-AGENT-POLICY-005",
        "PY-AGENT-POLICY-006",
        "PY-AGENT-POLICY-007",
        "PY-AGENT-POLICY-008",
        "PY-AGENT-POLICY-009",
        "PY-AGENT-POLICY-010",
        "PY-AGENT-POLICY-011",
        "PY-AGENT-POLICY-012",
    ]
    assert {rule.severity for rule in rules} == {PythonDiagnosticSeverity.INFO}
