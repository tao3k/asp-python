"""Native parser diagnostic rule pack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

from ._model import (
    AspPythonFinding,
    PythonRulePackDescriptor,
)
from ._syntax_catalog import SYNTAX_PACK_ID, syntax_rule

if TYPE_CHECKING:
    from collections.abc import Iterable

    from python_lang_parser import PythonModuleReport


@dataclass(frozen=True, slots=True)
class PythonSyntaxRulePack:
    """Rule pack that turns parser diagnostics into harness findings."""

    pack_id: str = SYNTAX_PACK_ID

    def descriptor(self) -> PythonRulePackDescriptor:
        """Return stable metadata for this rule pack."""

        return PythonRulePackDescriptor(
            id=self.pack_id,
            version="v1",
            domains=("syntax", "python"),
            default_mode="blocking",
        )

    def evaluate(self, report: PythonModuleReport) -> Iterable[AspPythonFinding]:
        """Evaluate parse diagnostics for one module report."""

        for diagnostic in report.diagnostics:
            if diagnostic.severity != PythonDiagnosticSeverity.ERROR:
                continue
            rule = syntax_rule(diagnostic.code)
            yield AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=self.pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=diagnostic.message,
                location=diagnostic.location,
                requirement=rule.requirement,
                source_line=diagnostic.source_line,
                label=diagnostic.message or diagnostic.label,
                labels=dict(rule.labels),
            )
