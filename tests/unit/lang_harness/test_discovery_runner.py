from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    AspPythonConfig,
    AspPythonFinding,
    PythonSyntaxRulePack,
    discover_python_files,
    render_python_lang_harness,
    run_asp_python,
    run_python_lang_harness,
)
from python_lang_parser import (
    PythonDiagnostic,
    PythonDiagnosticSeverity,
    PythonModuleReport,
    SourceLocation,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_discover_python_files_skips_cache_dirs(tmp_path: Path) -> None:
    src = tmp_path / "src"
    cache = src / "__pycache__"
    runtime_cache = tmp_path / ".cache"
    mirrored_data = tmp_path / ".data"
    src.mkdir()
    cache.mkdir()
    runtime_cache.mkdir()
    mirrored_data.mkdir()
    good = src / "good.py"
    ignored = cache / "ignored.py"
    runtime_ignored = runtime_cache / "ignored.py"
    data_ignored = mirrored_data / "ignored.py"
    good.write_text("VALUE = 1\n", encoding="utf-8")
    ignored.write_text("VALUE = 2\n", encoding="utf-8")
    runtime_ignored.write_text("VALUE = 3\n", encoding="utf-8")
    data_ignored.write_text("VALUE = 4\n", encoding="utf-8")

    assert discover_python_files([tmp_path]) == (good,)


def test_discover_python_files_skips_hidden_dirs_by_default(tmp_path: Path) -> None:
    src = tmp_path / "src"
    hidden = tmp_path / ".devenv"
    src.mkdir()
    hidden.mkdir()
    good = src / "good.py"
    ignored = hidden / "ignored.py"
    good.write_text("VALUE = 1\n", encoding="utf-8")
    ignored.write_text("VALUE = 2\n", encoding="utf-8")

    assert discover_python_files([tmp_path]) == (good,)


def test_asp_toml_can_include_hidden_python_dirs(tmp_path: Path) -> None:
    hidden = tmp_path / ".agent-fixtures"
    hidden.mkdir()
    fixture = hidden / "fixture.py"
    fixture.write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "asp.toml").write_text(
        '[discovery]\nincludeHiddenDirNames = [".agent-fixtures"]\n',
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert report.file_count == 1
    assert report.modules[0].path == str(fixture)


def test_discover_python_files_accepts_custom_ignored_dirs(tmp_path: Path) -> None:
    src = tmp_path / "src"
    generated = src / "generated"
    src.mkdir()
    generated.mkdir()
    good = src / "good.py"
    ignored = generated / "ignored.py"
    good.write_text("VALUE = 1\n", encoding="utf-8")
    ignored.write_text("VALUE = 2\n", encoding="utf-8")

    assert discover_python_files([tmp_path], ignored_dir_names={"generated"}) == (good,)


def test_discover_python_files_ignores_only_scan_relative_dirs(
    tmp_path: Path,
) -> None:
    project = tmp_path / "build" / "project"
    src = project / "src"
    ignored_dir = src / "build"
    src.mkdir(parents=True)
    ignored_dir.mkdir()
    good = src / "good.py"
    ignored = ignored_dir / "ignored.py"
    good.write_text("VALUE = 1\n", encoding="utf-8")
    ignored.write_text("VALUE = 2\n", encoding="utf-8")

    assert discover_python_files([project]) == (good,)


def test_discover_python_files_deduplicates_nested_scan_roots(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "good.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    assert discover_python_files([tmp_path, src]) == (source,)


def test_run_python_lang_harness_collects_parse_findings(tmp_path: Path) -> None:
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text(
        '"""Good module."""\n\n\ndef ok() -> None:\n    return None\n', encoding="utf-8"
    )
    bad.write_text("def broken(:\n    pass\n", encoding="utf-8")

    report = run_python_lang_harness([tmp_path])

    assert report.file_count == 2
    assert report.parsed_count == 1
    assert not report.is_clean
    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("python.syntax.invalid", str(bad)),
    ]
    assert report.to_dict()["is_clean"] is False


def test_run_python_lang_harness_uses_configured_discovery(tmp_path: Path) -> None:
    generated = tmp_path / "generated"
    generated.mkdir()
    ignored = generated / "debug.py"
    ignored.write_text('def run():\n    print("debug")\n', encoding="utf-8")

    report = run_python_lang_harness(
        [tmp_path],
        config=AspPythonConfig(ignored_dir_names=frozenset({"generated"})),
    )

    assert report.file_count == 0
    assert report.is_clean


def test_syntax_rule_pack_handles_unknown_parser_error_codes() -> None:
    report = PythonModuleReport(
        path="/repo/src/unreadable.py",
        module_docstring=None,
        diagnostics=(
            PythonDiagnostic(
                code="python.file.read_error",
                severity=PythonDiagnosticSeverity.ERROR,
                message="permission denied",
                location=SourceLocation(
                    path="/repo/src/unreadable.py",
                    line=1,
                    column=0,
                ),
                label="file could not be read",
                help="Check file permissions.",
            ),
        ),
    )

    findings = tuple(PythonSyntaxRulePack().evaluate(report))

    assert [(finding.rule_id, finding.title) for finding in findings] == [
        ("python.file.read_error", "Python parser emitted an error diagnostic"),
    ]
    assert findings[0].summary == "permission denied"


def test_run_python_lang_harness_uses_configured_blocking_severities(
    tmp_path: Path,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    config = AspPythonConfig(
        blocking_severities=frozenset({PythonDiagnosticSeverity.ERROR}),
        rule_packs=(_WarningRulePack(),),
    )

    report = run_python_lang_harness([source], config=config)

    assert [finding.rule_id for finding in report.findings] == [
        "python.project.warning"
    ]
    assert report.blocking_findings() == ()
    assert report.is_clean
    assert report.to_dict()["blocking_severities"] == ["error"]
    assert render_python_lang_harness(report).startswith("[ok]")


class _WarningRulePack:
    pack_id = "test.warning"

    def evaluate(self, report: PythonModuleReport) -> tuple[AspPythonFinding, ...]:
        return (
            AspPythonFinding(
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
