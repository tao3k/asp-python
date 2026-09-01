from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    PythonModernDesignRulePack,
    python_modern_design_rules,
    render_python_lang_harness,
    run_python_lang_harness,
)
from python_lang_parser import PythonDiagnosticSeverity

if TYPE_CHECKING:
    from pathlib import Path


def test_modern_design_rule_pack_reports_numbered_rules_in_compact_snapshot(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        'from tools import *\n\n\ndef run():\n    print("debug")\n    breakpoint()\n',
        encoding="utf-8",
    )

    output = render_python_lang_harness(
        run_python_lang_harness([source], rule_packs=(PythonModernDesignRulePack(),))
    )
    output = output.replace(str(source), "$TMP/module.py")

    assert output.startswith("[fail] python blockingFindings=3 parsed=1/1\n")
    assert (
        "|failureFrontier rule=PY-MOD-R001 severity=warning "
        "path=$TMP/module.py line=1 column=1"
    ) in output
    assert "|message Wildcard import hides the dependency surface" in output
    assert "|repair replace wildcard import with explicit imported names" in output
    assert (
        "|failureFrontier rule=PY-MOD-R002 severity=warning "
        "path=$TMP/module.py line=5 column=5"
    ) in output
    assert "|message Library module uses bare print" in output
    assert (
        "|repair replace bare print with a project-owned reporting surface"
    ) in output
    assert (
        "|failureFrontier rule=PY-MOD-R004 severity=warning "
        "path=$TMP/module.py line=6 column=5"
    ) in output
    assert "|message Library module contains breakpoint()" in output
    assert "|repair remove breakpoint() from library code" in output


def test_modern_design_rule_pack_requires_all_for_package_facade(
    tmp_path: Path,
) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    init_file = package / "__init__.py"
    init_file.write_text("from .api import Runner\n", encoding="utf-8")
    (package / "api.py").write_text("class Runner:\n    pass\n", encoding="utf-8")

    report = run_python_lang_harness(
        [package], rule_packs=(PythonModernDesignRulePack(),)
    )

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-MOD-R003", str(init_file)),
    ]


def test_modern_design_rule_pack_accepts_explicit_facade_all(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        'from .api import Runner\n\n__all__ = ["Runner"]\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text("class Runner:\n    pass\n", encoding="utf-8")

    report = run_python_lang_harness(
        [package], rule_packs=(PythonModernDesignRulePack(),)
    )

    assert report.is_clean


def test_modern_design_rule_pack_rejects_dynamic_facade_all(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    init_file = package / "__init__.py"
    init_file.write_text(
        "from .api import Runner\n\n__all__ = build_exports()\n",
        encoding="utf-8",
    )
    (package / "api.py").write_text("class Runner:\n    pass\n", encoding="utf-8")

    report = run_python_lang_harness(
        [package], rule_packs=(PythonModernDesignRulePack(),)
    )

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-MOD-R003", str(init_file)),
    ]


def test_modern_design_rule_pack_rejects_augmented_facade_all(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    init_file = package / "__init__.py"
    init_file.write_text(
        'from .api import Runner\n\n__all__ = ["Runner"]\n__all__ += ["Other"]\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text("class Runner:\n    pass\n", encoding="utf-8")

    report = run_python_lang_harness(
        [package], rule_packs=(PythonModernDesignRulePack(),)
    )

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-MOD-R003", str(init_file)),
    ]


def test_modern_design_rule_pack_skips_prints_in_tests(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    source = tests / "test_debug.py"
    source.write_text(
        'def test_debug():\n    print("debug")\n    breakpoint()\n',
        encoding="utf-8",
    )

    report = run_python_lang_harness(
        [tmp_path], rule_packs=(PythonModernDesignRulePack(),)
    )

    assert report.is_clean


def test_modern_design_rule_pack_descriptor_is_stable() -> None:
    descriptor = PythonModernDesignRulePack().descriptor()

    assert descriptor.id == "python.modern_design"
    assert descriptor.version == "v1"
    assert descriptor.default_mode == "blocking"
    assert descriptor.to_dict()["domains"] == ["modern-python", "design", "python"]


def test_modern_design_rule_catalog_is_compact_and_stable() -> None:
    rules = python_modern_design_rules()

    assert [rule.rule_id for rule in rules] == [
        "PY-MOD-R001",
        "PY-MOD-R002",
        "PY-MOD-R003",
        "PY-MOD-R004",
    ]
    assert {rule.pack_id for rule in rules} == {"python.modern_design"}
    assert {rule.severity for rule in rules} == {PythonDiagnosticSeverity.WARNING}
    assert rules[-1].to_dict() == {
        "rule_id": "PY-MOD-R004",
        "pack_id": "python.modern_design",
        "severity": "warning",
        "title": "Library module contains breakpoint()",
        "requirement": "Remove `breakpoint()` from library modules; use test-only debug tooling or a project-owned diagnostic surface.",
        "labels": {"language": "python", "domain": "modern-python"},
    }
