"""Project-scope rule-pack evaluation helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._agent_policy_catalog import PY_AGENT_R002
from ._project_policy_catalog import PY_PROJ_R004

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonModuleReport

    from ._model import (
        PythonHarnessFinding,
        PythonLangRulePack,
        PythonProjectHarnessScope,
    )


def evaluate_project_rule_packs(
    scope: PythonProjectHarnessScope,
    rule_packs: Sequence[PythonLangRulePack],
    modules: Sequence[PythonModuleReport],
) -> tuple[PythonHarnessFinding, ...]:
    """Evaluate project-resolution hooks exposed by configured rule packs."""

    findings: list[PythonHarnessFinding] = []
    for rule_pack in rule_packs:
        module_evaluator = getattr(rule_pack, "evaluate_project_modules", None)
        if module_evaluator is not None:
            findings.extend(module_evaluator(scope, modules))
            continue
        scope_evaluator = getattr(rule_pack, "evaluate_project_resolution", None)
        if scope_evaluator is not None:
            findings.extend(scope_evaluator(scope))
            continue
        evaluator = getattr(rule_pack, "evaluate_project", None)
        if evaluator is None:
            continue
        findings.extend(evaluator(scope.project_root))
    return tuple(findings)


def compact_project_findings(
    module_findings: Sequence[PythonHarnessFinding],
    project_findings: Sequence[PythonHarnessFinding],
) -> tuple[PythonHarnessFinding, ...]:
    """Remove duplicate module advice covered by stricter project findings."""

    typed_package_annotation_locations = {
        _finding_location_key(finding)
        for finding in project_findings
        if finding.rule_id == PY_PROJ_R004
    }
    compact_module_findings = tuple(
        finding
        for finding in module_findings
        if not (
            finding.rule_id == PY_AGENT_R002
            and _finding_location_key(finding) in typed_package_annotation_locations
        )
    )
    return (*compact_module_findings, *project_findings)


def _finding_location_key(
    finding: PythonHarnessFinding,
) -> tuple[str | None, int, int]:
    return (
        finding.location.path,
        finding.location.line,
        finding.location.column,
    )
