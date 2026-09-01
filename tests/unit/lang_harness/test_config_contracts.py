from __future__ import annotations

import json
from typing import TYPE_CHECKING

from asp_python import (
    default_python_harness_config,
    python_rule_pack_descriptors,
    python_syntax_rules,
    render_python_lang_harness_json,
    run_python_lang_harness,
)
from python_lang_parser import PythonDiagnosticSeverity

if TYPE_CHECKING:
    from pathlib import Path


def test_default_python_harness_config_uses_default_rule_packs() -> None:
    config = default_python_harness_config()

    assert config.ignored_dir_names
    assert config.blocking_severities == {
        PythonDiagnosticSeverity.ERROR,
        PythonDiagnosticSeverity.WARNING,
    }
    assert config.include_tests is True
    assert config.source_dir_names == ("src",)
    assert config.test_dir_names == ("tests",)
    assert config.extra_path_names == ()
    assert config.disabled_rule_ids == frozenset()
    assert config.blocking_rule_ids == frozenset()
    assert [rule_pack.pack_id for rule_pack in config.rule_packs or ()] == [
        "python.syntax",
        "python.project_policy",
        "python.modern_design",
        "python.modularity",
        "python.test_layout",
        "python.agent_policy",
    ]


def test_rule_pack_descriptors_and_json_renderer_are_stable(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text('"""Module docs."""\n\nVALUE = 1\n', encoding="utf-8")

    report = run_python_lang_harness([source])
    payload = json.loads(render_python_lang_harness_json(report))

    assert [descriptor.id for descriptor in python_rule_pack_descriptors()] == [
        "python.syntax",
        "python.project_policy",
        "python.modern_design",
        "python.modularity",
        "python.test_layout",
        "python.agent_policy",
    ]
    assert [
        descriptor.default_mode for descriptor in python_rule_pack_descriptors()
    ] == [
        "blocking",
        "blocking",
        "blocking",
        "blocking",
        "blocking",
        "advisory",
    ]
    assert payload["file_count"] == 1
    assert payload["disabled_rule_ids"] == []
    assert payload["blocking_rule_ids"] == []
    assert payload["modules"][0]["metadata"]["parser"] == "cpython.ast"


def test_syntax_rule_catalog_is_stable() -> None:
    rules = python_syntax_rules()

    assert [rule.rule_id for rule in rules] == [
        "python.syntax.invalid",
        "python.compile.invalid",
    ]
    assert {rule.pack_id for rule in rules} == {"python.syntax"}
    assert {rule.severity for rule in rules} == {PythonDiagnosticSeverity.ERROR}
