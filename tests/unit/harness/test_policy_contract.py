from __future__ import annotations

from pathlib import Path

from python_lang_parser import PythonDiagnosticSeverity
from python_lang_project_harness import (
    default_python_harness_config,
    python_agent_policy_rules,
    python_modern_design_rules,
    python_modularity_rules,
    python_project_policy_rules,
    python_rule_pack_descriptors,
    python_syntax_rules,
    python_test_layout_rules,
    render_python_lang_harness,
    run_python_project_harness,
)

_PROJECT_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").exists() and (parent / "src").exists()
)
_SNAPSHOT_ROOT = _PROJECT_ROOT / "tests" / "unit" / "snapshots"
_RULE_CATALOG_DOC = _PROJECT_ROOT / "docs" / "03_features" / "201_rule_catalog.md"
_REDUNDANT_AGENT_RENDER_LINES = (
    "[lint:",
    "[ok]",
    "Source:",
    "Issues:",
    "No blocking issues found.",
)
_REDUNDANT_TREE_RENDER_LINES = (
    "Files:",
    "Nodes:",
)
_EXPECTED_RULE_SNAPSHOT_FILES = {
    "unit_test__agent_policy_snapshot__py_agent_r001_module_intent.snap",
    "unit_test__agent_policy_snapshot__py_agent_r002_callable_annotations.snap",
    "unit_test__agent_policy_snapshot__py_agent_r003_callable_conflict.snap",
    "unit_test__agent_policy_snapshot__py_agent_r004_repeated_namespace.snap",
    "unit_test__agent_policy_snapshot__py_agent_r005_type_conflict.snap",
    "unit_test__agent_policy_snapshot__py_agent_r006_value_conflict.snap",
    "unit_test__agent_policy_snapshot__py_agent_r007_branch_intent.snap",
    "unit_test__agent_policy_snapshot__py_agent_r008_branch_surface.snap",
    "unit_test__agent_policy_snapshot__py_agent_r009_algorithm_shape.snap",
    "unit_test__agent_policy_snapshot__py_agent_r010_function_compactness.snap",
    "unit_test__agent_policy_snapshot__py_agent_r011_native_idiom.snap",
    "unit_test__agent_policy_snapshot__py_agent_r012_type_shape.snap",
    "unit_test__policy_snapshot__py_mod_r001_wildcard_import.snap",
    "unit_test__policy_snapshot__py_mod_r002_bare_print.snap",
    "unit_test__policy_snapshot__py_mod_r003_facade_all.snap",
    "unit_test__policy_snapshot__py_mod_r004_breakpoint.snap",
    "unit_test__policy_snapshot__py_mod_r006_module_bloat.snap",
    "unit_test__policy_snapshot__py_mod_r007_reasoning_tree_shadow.snap",
    "unit_test__policy_snapshot__py_proj_r001_src_layout.snap",
    "unit_test__policy_snapshot__py_proj_r002_declared_package.snap",
    "unit_test__policy_snapshot__py_proj_r003_py_typed.snap",
    "unit_test__policy_snapshot__py_proj_r004_typed_annotations.snap",
    "unit_test__policy_snapshot__py_proj_r005_project_name.snap",
    "unit_test__policy_snapshot__py_proj_r006_requires_python.snap",
    "unit_test__policy_snapshot__py_proj_r007_build_requires.snap",
    "unit_test__policy_snapshot__py_proj_r008_import_names.snap",
    "unit_test__policy_snapshot__py_proj_r009_entry_point_target.snap",
    "unit_test__policy_snapshot__py_proj_r010_pytest_gate.snap",
    "unit_test__policy_snapshot__py_proj_r011_verification_profile.snap",
    "unit_test__policy_snapshot__py_test_r001_root_pytest.snap",
    "unit_test__policy_snapshot__py_test_r002_unexpected_root.snap",
    "unit_test__policy_snapshot__py_test_r003_unit_bloat.snap",
    "unit_test__policy_snapshot__python_compile_invalid.snap",
    "unit_test__policy_snapshot__python_syntax_invalid.snap",
}


def test_default_policy_blocks_only_warning_and_error() -> None:
    config = default_python_harness_config()

    assert config.blocking_severities == {
        PythonDiagnosticSeverity.ERROR,
        PythonDiagnosticSeverity.WARNING,
    }


def test_agent_policy_rules_are_non_blocking_advice() -> None:
    assert {rule.severity for rule in python_agent_policy_rules()} == {
        PythonDiagnosticSeverity.INFO
    }


def test_rule_pack_descriptors_expose_default_execution_order() -> None:
    descriptors = python_rule_pack_descriptors()

    assert [descriptor.id for descriptor in descriptors] == [
        "python.syntax",
        "python.project_policy",
        "python.modern_design",
        "python.modularity",
        "python.test_layout",
        "python.agent_policy",
    ]
    assert [descriptor.default_mode for descriptor in descriptors] == [
        "blocking",
        "blocking",
        "blocking",
        "blocking",
        "blocking",
        "advisory",
    ]
    assert {descriptor.version for descriptor in descriptors} == {"v1"}
    assert all("python" in descriptor.domains for descriptor in descriptors)


def test_rule_catalogs_expose_stable_rule_ids() -> None:
    assert [rule.rule_id for rule in python_syntax_rules()] == [
        "python.syntax.invalid",
        "python.compile.invalid",
    ]
    assert [rule.rule_id for rule in python_project_policy_rules()] == [
        "PY-AGENT-PROJECT-001",
        "PY-AGENT-PROJECT-002",
        "PY-AGENT-PROJECT-003",
        "PY-AGENT-PROJECT-004",
        "PY-AGENT-PROJECT-005",
        "PY-AGENT-PROJECT-006",
        "PY-AGENT-PROJECT-007",
        "PY-AGENT-PROJECT-008",
        "PY-AGENT-PROJECT-009",
        "PY-AGENT-PROJECT-010",
        "PY-AGENT-PROJECT-011",
    ]
    assert [rule.rule_id for rule in python_modern_design_rules()] == [
        "PY-MOD-R001",
        "PY-MOD-R002",
        "PY-MOD-R003",
        "PY-MOD-R004",
    ]
    assert [rule.rule_id for rule in python_modularity_rules()] == [
        "PY-MOD-R006",
        "PY-MOD-R007",
    ]
    assert [rule.rule_id for rule in python_agent_policy_rules()] == [
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
    assert [rule.rule_id for rule in python_test_layout_rules()] == [
        "PY-TEST-R001",
        "PY-TEST-R002",
        "PY-TEST-R003",
    ]


def test_rule_catalogs_keep_default_severities_aligned() -> None:
    assert {rule.severity for rule in python_syntax_rules()} == {
        PythonDiagnosticSeverity.ERROR
    }
    assert [rule.severity for rule in python_project_policy_rules()] == [
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.WARNING,
        PythonDiagnosticSeverity.INFO,
    ]
    assert {rule.severity for rule in python_modern_design_rules()} == {
        PythonDiagnosticSeverity.WARNING
    }
    assert {rule.severity for rule in python_modularity_rules()} == {
        PythonDiagnosticSeverity.WARNING
    }
    assert {rule.severity for rule in python_test_layout_rules()} == {
        PythonDiagnosticSeverity.WARNING
    }
    assert {rule.severity for rule in python_agent_policy_rules()} == {
        PythonDiagnosticSeverity.INFO
    }


def test_rule_catalog_doc_lists_every_default_rule() -> None:
    document = _RULE_CATALOG_DOC.read_text(encoding="utf-8")

    for rule_id in _all_default_rule_ids():
        assert f"`{rule_id}`" in document, rule_id


def test_policy_snapshots_cover_every_catalog_rule() -> None:
    snapshot_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(_SNAPSHOT_ROOT.glob("*.snap"))
    )

    for rule_id in _all_default_rule_ids():
        assert any(
            token in snapshot_text
            for token in (
                f"rule={rule_id} ",
                f'"rule_id":"{rule_id}"',
                f'"rule_id": "{rule_id}"',
                f"[{rule_id}]",
            )
        ), rule_id


def test_rule_snapshot_files_have_no_stale_policy_baselines() -> None:
    actual_rule_snapshots = {
        path.name
        for pattern in (
            "unit_test__agent_policy_snapshot__*.snap",
            "unit_test__policy_snapshot__*.snap",
        )
        for path in _SNAPSHOT_ROOT.glob(pattern)
    }

    assert actual_rule_snapshots == _EXPECTED_RULE_SNAPSHOT_FILES


def test_agent_facing_snapshots_avoid_redundant_render_preambles() -> None:
    for snapshot in _SNAPSHOT_ROOT.glob("unit_test__agent_policy_snapshot__*.snap"):
        text = snapshot.read_text(encoding="utf-8")
        for line in _REDUNDANT_AGENT_RENDER_LINES:
            assert line not in text, snapshot.name

    tree_text = (_SNAPSHOT_ROOT / "python_project_reasoning_tree.snap").read_text(
        encoding="utf-8"
    )
    for line in _REDUNDANT_TREE_RENDER_LINES:
        assert line not in tree_text


def test_project_is_clean_under_its_own_harness() -> None:
    report = run_python_project_harness(_PROJECT_ROOT)
    rendered = render_python_lang_harness(report)

    assert report.is_clean, rendered
    assert "[fail]" not in rendered
    assert "[advice]" in rendered


def _all_default_rule_ids() -> tuple[str, ...]:
    return tuple(
        rule.rule_id
        for rules in (
            python_syntax_rules(),
            python_project_policy_rules(),
            python_modern_design_rules(),
            python_modularity_rules(),
            python_agent_policy_rules(),
            python_test_layout_rules(),
        )
        for rule in rules
    )
