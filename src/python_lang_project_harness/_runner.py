"""Runner API for embedding the Python language harness in pytest."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity
from python_lang_parser.parser import parse_python_file

from ._discovery import discover_python_files, python_project_harness_scope
from ._model import (
    PythonHarnessConfig,
    PythonHarnessFinding,
    PythonHarnessReport,
    PythonLangRulePack,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def run_python_project_harness(
    project_root: str | Path,
    *,
    config: PythonHarnessConfig | None = None,
    rule_packs: Sequence[PythonLangRulePack] | None = None,
    include_tests: bool | None = None,
    source_dir_names: Sequence[str] | None = None,
    test_dir_names: Sequence[str] | None = None,
    extra_path_names: Sequence[str] | None = None,
) -> PythonHarnessReport:
    """Run the harness over conventional Python project paths."""

    root = Path(project_root)
    if not root.exists():
        raise ValueError(f"project root does not exist: {root}")
    from ._project_evaluation import (
        compact_project_findings,
        evaluate_project_rule_packs,
    )
    from ._rule_packs import resolve_project_harness_config, selected_rule_packs

    selected_config = resolve_project_harness_config(
        root,
        config,
        rule_packs=rule_packs,
    )
    selected_packs = selected_rule_packs(selected_config)
    scope = python_project_harness_scope(
        root,
        include_tests=(
            selected_config.include_tests if include_tests is None else include_tests
        ),
        source_dir_names=(
            selected_config.source_dir_names
            if source_dir_names is None
            else tuple(source_dir_names)
        ),
        test_dir_names=(
            selected_config.test_dir_names
            if test_dir_names is None
            else tuple(test_dir_names)
        ),
        extra_path_names=(
            selected_config.extra_path_names
            if extra_path_names is None
            else tuple(extra_path_names)
        ),
        ignored_dir_names=selected_config.ignored_dir_names,
        include_hidden_dir_names=selected_config.include_hidden_dir_names,
    )
    report = run_python_lang_harness(
        scope.monitored_paths,
        config=selected_config,
    )
    project_findings = evaluate_project_rule_packs(
        scope,
        selected_packs,
        report.modules,
    )
    return replace(
        report,
        project_resolution=scope,
        findings=_configured_findings(
            compact_project_findings(report.findings, project_findings),
            config=selected_config,
        ),
    )


def assert_python_project_harness_clean(
    project_root: str | Path,
    *,
    config: PythonHarnessConfig | None = None,
    rule_packs: Sequence[PythonLangRulePack] | None = None,
    severities: frozenset[PythonDiagnosticSeverity] | None = None,
    include_tests: bool | None = None,
    source_dir_names: Sequence[str] | None = None,
    test_dir_names: Sequence[str] | None = None,
    extra_path_names: Sequence[str] | None = None,
    include_advice: bool = True,
) -> PythonHarnessReport:
    """Run the project harness and raise when configured-blocking findings exist."""

    from ._rule_packs import resolve_project_harness_config

    selected_config = resolve_project_harness_config(
        Path(project_root),
        config,
        rule_packs=rule_packs,
    )
    report = run_python_project_harness(
        project_root,
        config=selected_config,
        include_tests=include_tests,
        source_dir_names=source_dir_names,
        test_dir_names=test_dir_names,
        extra_path_names=extra_path_names,
    )
    report.assert_clean(
        severities=(
            severities
            if severities is not None
            else selected_config.blocking_severities
        ),
        include_advice=include_advice,
    )
    return report


def run_python_lang_harness(
    paths: Sequence[str | Path],
    *,
    config: PythonHarnessConfig | None = None,
    rule_packs: Sequence[PythonLangRulePack] | None = None,
) -> PythonHarnessReport:
    """Run the Python language harness over files or directories."""

    if rule_packs == ():
        selected_config = (
            replace(config, rule_packs=())
            if config is not None
            else PythonHarnessConfig(rule_packs=())
        )
        selected_packs = ()
    else:
        from ._rule_packs import resolve_harness_config, selected_rule_packs

        selected_config = resolve_harness_config(config, rule_packs=rule_packs)
        selected_packs = selected_rule_packs(selected_config)
    root_paths = tuple(Path(path) for path in paths)
    for path in root_paths:
        if not path.exists():
            raise ValueError(f"harness path does not exist: {path}")
    modules = tuple(
        parse_python_file(path)
        for path in discover_python_files(
            root_paths,
            ignored_dir_names=selected_config.ignored_dir_names,
            include_hidden_dir_names=selected_config.include_hidden_dir_names,
        )
    )
    findings = tuple(
        finding
        for module in modules
        for rule_pack in selected_packs
        for finding in rule_pack.evaluate(module)
    )
    return PythonHarnessReport(
        modules=modules,
        findings=_configured_findings(findings, config=selected_config),
        root_paths=tuple(str(path) for path in root_paths),
        blocking_severities=selected_config.blocking_severities,
        disabled_rule_ids=selected_config.disabled_rule_ids,
        blocking_rule_ids=selected_config.blocking_rule_ids,
    )


def assert_python_lang_harness_clean(
    paths: Sequence[str | Path],
    *,
    config: PythonHarnessConfig | None = None,
    rule_packs: Sequence[PythonLangRulePack] | None = None,
    severities: frozenset[PythonDiagnosticSeverity] | None = None,
    include_advice: bool = True,
) -> PythonHarnessReport:
    """Run the harness and raise when configured-blocking findings are present."""

    from ._rule_packs import resolve_harness_config

    selected_config = resolve_harness_config(config, rule_packs=rule_packs)
    report = run_python_lang_harness(paths, config=selected_config)
    report.assert_clean(
        severities=(
            severities
            if severities is not None
            else selected_config.blocking_severities
        ),
        include_advice=include_advice,
    )
    return report


def _configured_findings(
    findings: tuple[PythonHarnessFinding, ...],
    *,
    config: PythonHarnessConfig,
) -> tuple[PythonHarnessFinding, ...]:
    if not config.disabled_rule_ids:
        return findings
    return tuple(
        finding
        for finding in findings
        if finding.rule_id not in config.disabled_rule_ids
    )
