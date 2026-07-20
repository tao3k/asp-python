from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_parser import PythonDiagnosticSeverity, SourceLocation
from python_lang_project_harness import (
    PythonHarnessConfig,
    PythonHarnessFinding,
    assert_python_lang_harness_clean,
    render_python_lang_harness,
    run_python_lang_harness,
)

if TYPE_CHECKING:
    from pathlib import Path

    from python_lang_parser import PythonModuleReport


def test_render_python_lang_harness_uses_compact_source_diagnostic(
    tmp_path: Path,
) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(:\n    pass\n", encoding="utf-8")

    output = render_python_lang_harness(run_python_lang_harness([bad]))

    assert output.startswith("[fail] python blockingFindings=1 parsed=0/1")
    assert "|failureFrontier rule=python.syntax.invalid severity=error" in output
    assert "|hotBlock selector=" in output
    assert "bad.py:1:1 reason=blocking-finding" in output
    assert "|next action=" not in output
    assert "owner-local-projection" not in output
    assert "Action:" not in output
    assert "Fix:" not in output
    assert "Evidence:" not in output


def test_render_python_lang_harness_attaches_agent_advice_by_default(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("def run(value):\n    print(value)\n", encoding="utf-8")
    report = run_python_lang_harness([source])

    default_output = render_python_lang_harness(report)
    quiet_output = render_python_lang_harness(report, include_advice=False)

    assert default_output.startswith("[fail] python blockingFindings=1 parsed=1/1")
    assert "|failureFrontier rule=PY-MOD-R002 severity=warning" in default_output
    assert "|hotBlock selector=" in default_output
    assert "\n[advice]\n[PY-AGENT-POLICY-001]" in default_output
    assert (
        "[PY-AGENT-POLICY-001] Info: Library module lacks a module intent docstring"
        in default_output
    )
    assert (
        "[PY-AGENT-POLICY-002] Info: Public callable lacks type annotations"
        in default_output
    )
    assert "PY-AGENT" not in quiet_output


def test_assert_python_lang_harness_clean_blocks_for_pytest(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(:\n    pass\n", encoding="utf-8")

    try:
        assert_python_lang_harness_clean([bad])
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("harness should block invalid Python source")

    assert "[fail] python blockingFindings=1 parsed=0/1" in message
    assert "python.syntax.invalid" in message


def test_assert_python_lang_harness_clean_includes_agent_advice_by_default(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("def run(value):\n    print(value)\n", encoding="utf-8")

    try:
        assert_python_lang_harness_clean([source])
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("harness should block warning findings")

    assert "[advice]" in message
    assert (
        "[PY-AGENT-POLICY-001] Info: Library module lacks a module intent docstring"
        in message
    )


def test_assert_python_lang_harness_clean_can_disable_agent_advice(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("def run(value):\n    print(value)\n", encoding="utf-8")

    try:
        assert_python_lang_harness_clean([source], include_advice=False)
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("harness should block warning findings")

    assert "[fail] python blockingFindings=1 parsed=1/1" in message
    assert "|failureFrontier rule=PY-MOD-R002 severity=warning" in message
    assert "[advice]" not in message


def test_assert_python_lang_harness_clean_blocks_warning_findings(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    try:
        assert_python_lang_harness_clean([source], rule_packs=(_WarningRulePack(),))
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("harness should block warning findings")

    assert "[fail] python blockingFindings=1 parsed=1/1" in message
    assert "|failureFrontier rule=python.project.warning severity=warning" in message


def test_assert_python_lang_harness_clean_honors_configured_blocking_severities(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    config = PythonHarnessConfig(
        blocking_severities=frozenset({PythonDiagnosticSeverity.ERROR}),
        rule_packs=(_WarningRulePack(),),
    )

    report = assert_python_lang_harness_clean([source], config=config)

    assert [finding.rule_id for finding in report.findings] == [
        "python.project.warning"
    ]
    assert report.is_clean


def test_assert_python_lang_harness_clean_honors_severities_override(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    config = PythonHarnessConfig(
        blocking_severities=frozenset({PythonDiagnosticSeverity.ERROR}),
        rule_packs=(_WarningRulePack(),),
    )

    try:
        assert_python_lang_harness_clean(
            [source],
            config=config,
            severities=frozenset({PythonDiagnosticSeverity.WARNING}),
        )
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("severity override should still block warnings")

    assert "[fail] python blockingFindings=1 parsed=1/1" in message
    assert "|failureFrontier rule=python.project.warning severity=warning" in message


class _WarningRulePack:
    pack_id = "test.warning"

    def evaluate(self, report: PythonModuleReport) -> tuple[PythonHarnessFinding, ...]:
        return (
            PythonHarnessFinding(
                rule_id="python.project.warning",
                pack_id=self.pack_id,
                severity=PythonDiagnosticSeverity.WARNING,
                title="Project warning",
                summary="warning emitted by a project rule",
                location=SourceLocation(path=report.path, line=1, column=0),
                requirement="Fix the project rule warning.",
                source_line="VALUE = 1",
            ),
        )
