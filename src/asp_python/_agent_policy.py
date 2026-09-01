"""Agent-oriented Python policy rules backed by native parser reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser import (
    python_module_has_public_symbol_surface,
    python_symbol_is_public_callable,
)

from ._agent_namespace import agent_namespace_findings
from ._agent_policy_catalog import (
    AGENT_POLICY_PACK_ID,
    PY_AGENT_R001,
    PY_AGENT_R002,
    agent_policy_rule,
)
from ._agent_reasoning_tree import agent_reasoning_tree_findings
from ._model import AspPythonFinding, PythonRulePackDescriptor
from ._source import path_location
from .agent_readability import (
    agent_algorithm_shape_findings,
    agent_function_compactness_findings,
    agent_native_idiom_findings,
    agent_type_shape_findings,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from python_lang_parser import PythonModuleReport, PythonSymbol

    from ._model import PythonProjectHarnessScope


@dataclass(frozen=True, slots=True)
class PythonAgentPolicyRulePack:
    """Rules that keep Python projects legible for repair-oriented agents."""

    pack_id: str = AGENT_POLICY_PACK_ID

    def descriptor(self) -> PythonRulePackDescriptor:
        """Return stable metadata for this rule pack."""

        return PythonRulePackDescriptor(
            id=self.pack_id,
            version="v1",
            domains=("agent-policy", "project-shape", "python"),
            default_mode="advisory",
        )

    def evaluate(self, report: PythonModuleReport) -> Iterable[AspPythonFinding]:
        """Evaluate agent-oriented policy rules for one parsed module report."""

        if not report.is_valid:
            return ()

        findings: list[AspPythonFinding] = []
        findings.extend(_module_docstring_findings(report, self.pack_id))
        findings.extend(_public_callable_annotation_findings(report, self.pack_id))
        findings.extend(agent_algorithm_shape_findings(report, self.pack_id))
        findings.extend(agent_function_compactness_findings(report, self.pack_id))
        findings.extend(agent_native_idiom_findings(report, self.pack_id))
        findings.extend(agent_type_shape_findings(report, self.pack_id))
        return tuple(findings)

    def evaluate_project_modules(
        self,
        scope: PythonProjectHarnessScope,
        modules: Sequence[PythonModuleReport],
    ) -> Iterable[AspPythonFinding]:
        """Evaluate agent-oriented namespace rules across a project scope."""

        return (
            *agent_namespace_findings(scope, modules, self.pack_id),
            *agent_reasoning_tree_findings(scope, modules, self.pack_id),
        )


def _module_docstring_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    if report.module_docstring or not _module_has_agent_surface(report):
        return ()
    rule = agent_policy_rule(PY_AGENT_R001)
    path = Path(report.path or "<memory>")
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=f"{path.name} has public module surface without a module intent docstring.",
            location=path_location(path),
            requirement=rule.requirement,
            source_line=report.source_line(1),
            label="add a concise module responsibility docstring",
            labels=dict(rule.labels),
        ),
    )


def _public_callable_annotation_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    findings: list[AspPythonFinding] = []
    rule = agent_policy_rule(PY_AGENT_R002)
    for symbol in report.symbols:
        if not _is_public_callable(symbol) or symbol.has_annotations:
            continue
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=f"{symbol.qualified_name} exposes a public callable boundary without annotations.",
                location=symbol.location,
                requirement=rule.requirement,
                source_line=report.source_line(symbol.location.line),
                label="add parameter and return annotations to this public callable",
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)


def _module_has_agent_surface(report: PythonModuleReport) -> bool:
    return python_module_has_public_symbol_surface(report)


def _is_public_callable(symbol: PythonSymbol) -> bool:
    return python_symbol_is_public_callable(symbol)
