"""Runner API for embedding the ASP Python in pytest."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity
from python_lang_parser.model import PythonModuleReport
from python_lang_parser.parser import parse_python_file

from ._discovery import asp_python_scope, discover_python_files
from ._model import (
    AspPythonConfig,
    AspPythonFinding,
    AspPythonReport,
    AspPythonRulePack,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def run_asp_python(
    project_root: str | Path,
    *,
    config: AspPythonConfig | None = None,
    rule_packs: Sequence[AspPythonRulePack] | None = None,
    include_tests: bool | None = None,
    source_dir_names: Sequence[str] | None = None,
    test_dir_names: Sequence[str] | None = None,
    extra_path_names: Sequence[str] | None = None,
) -> AspPythonReport:
    """Run ASP Python over conventional Python project paths."""

    root = Path(project_root)
    if not root.exists():
        raise ValueError(f"project root does not exist: {root}")
    from ._project_evaluation import (
        compact_project_findings,
        evaluate_project_rule_packs,
    )
    from ._rule_packs import resolve_asp_python_project_config, selected_rule_packs

    selected_config = resolve_asp_python_project_config(
        root,
        config,
        rule_packs=rule_packs,
    )
    selected_packs = selected_rule_packs(selected_config)
    scope = asp_python_scope(
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
    report = run_asp_python_paths(
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


def assert_asp_python_clean(
    project_root: str | Path,
    *,
    config: AspPythonConfig | None = None,
    rule_packs: Sequence[AspPythonRulePack] | None = None,
    severities: frozenset[PythonDiagnosticSeverity] | None = None,
    include_tests: bool | None = None,
    source_dir_names: Sequence[str] | None = None,
    test_dir_names: Sequence[str] | None = None,
    extra_path_names: Sequence[str] | None = None,
    include_advice: bool = True,
) -> AspPythonReport:
    """Run the ASP Python and raise when configured-blocking findings exist."""

    from ._rule_packs import resolve_asp_python_project_config

    selected_config = resolve_asp_python_project_config(
        Path(project_root),
        config,
        rule_packs=rule_packs,
    )
    report = run_asp_python(
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


def run_asp_python_paths(
    paths: Sequence[str | Path],
    *,
    config: AspPythonConfig | None = None,
    rule_packs: Sequence[AspPythonRulePack] | None = None,
) -> AspPythonReport:
    """Run the ASP Python over files or directories."""

    if rule_packs == ():
        selected_config = (
            replace(config, rule_packs=())
            if config is not None
            else AspPythonConfig(rule_packs=())
        )
        selected_packs = ()
    else:
        from ._rule_packs import resolve_asp_python_config, selected_rule_packs

        selected_config = resolve_asp_python_config(config, rule_packs=rule_packs)
        selected_packs = selected_rule_packs(selected_config)
    root_paths = tuple(Path(path) for path in paths)
    for path in root_paths:
        if not path.exists():
            raise ValueError(f"ASP Python path does not exist: {path}")
    modules = _parse_python_files(
        discover_python_files(
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
    return AspPythonReport(
        modules=modules,
        findings=_configured_findings(findings, config=selected_config),
        root_paths=tuple(str(path) for path in root_paths),
        blocking_severities=selected_config.blocking_severities,
        disabled_rule_ids=selected_config.disabled_rule_ids,
        blocking_rule_ids=selected_config.blocking_rule_ids,
    )


def _parse_python_files(paths: Sequence[Path]) -> tuple[PythonModuleReport, ...]:
    """Parse independent files concurrently while retaining discovery order."""

    if len(paths) < 2:
        return tuple(parse_python_file(path) for path in paths)
    with ThreadPoolExecutor(thread_name_prefix="asp-python-parse") as executor:
        return tuple(executor.map(parse_python_file, paths))


def assert_asp_python_paths_clean(
    paths: Sequence[str | Path],
    *,
    config: AspPythonConfig | None = None,
    rule_packs: Sequence[AspPythonRulePack] | None = None,
    severities: frozenset[PythonDiagnosticSeverity] | None = None,
    include_advice: bool = True,
) -> AspPythonReport:
    """Run ASP Python and raise when configured-blocking findings are present."""

    from ._rule_packs import resolve_asp_python_config

    selected_config = resolve_asp_python_config(config, rule_packs=rule_packs)
    report = run_asp_python_paths(paths, config=selected_config)
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
    findings: tuple[AspPythonFinding, ...],
    *,
    config: AspPythonConfig,
) -> tuple[AspPythonFinding, ...]:
    if not config.disabled_rule_ids:
        return findings
    return tuple(
        finding
        for finding in findings
        if finding.rule_id not in config.disabled_rule_ids
    )
