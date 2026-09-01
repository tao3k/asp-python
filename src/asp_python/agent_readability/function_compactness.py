"""Agent-facing compact-function advice from parser-owned function facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._agent_policy_catalog import PY_AGENT_R010, agent_policy_rule
from .._model import AspPythonFinding
from ._boundaries import (
    agent_readability_function_is_boundary,
    agent_readability_public_class_scopes,
    agent_readability_report_is_in_scope,
)
from ._software_criteria import CONTROL_FLOW_BROAD_LINEAR_PHASE, finding_labels

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonFunctionControlFlow,
        PythonModuleReport,
        PythonSymbol,
    )

_MAX_PUBLIC_FUNCTION_LINES = 72
_MAX_LINEAR_BLOCK_STATEMENTS = 14
_MAX_TOTAL_STATEMENTS = 22
_MAX_NESTING_FOR_LINEAR_RULE = 2


def agent_function_compactness_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return machine-readability advice for broad public function bodies."""

    if not agent_readability_report_is_in_scope(report):
        return ()
    findings: list[AspPythonFinding] = []
    rule = agent_policy_rule(PY_AGENT_R010)
    public_class_scopes = agent_readability_public_class_scopes(report)
    for symbol in report.symbols:
        control_flow = symbol.control_flow
        if (
            not agent_readability_function_is_boundary(
                symbol,
                public_class_scopes=public_class_scopes,
            )
            or control_flow is None
        ):
            continue
        line_span = _symbol_line_span(symbol)
        profile = _compactness_profile(control_flow, line_span=line_span)
        if not profile:
            continue
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=_summary(symbol, control_flow, line_span=line_span),
                location=symbol.location,
                requirement=f"{rule.requirement} Criteria: {', '.join(profile)}.",
                source_line=report.source_line(symbol.location.line),
                label="split this broad function into named algorithm steps",
                labels=finding_labels(
                    dict(rule.labels),
                    (CONTROL_FLOW_BROAD_LINEAR_PHASE,),
                ),
            )
        )
    return tuple(findings)


def _compactness_profile(
    control_flow: PythonFunctionControlFlow,
    *,
    line_span: int,
) -> tuple[str, ...]:
    if control_flow.max_nesting_depth > _MAX_NESTING_FOR_LINEAR_RULE:
        return ()
    indicators: list[str] = []
    if (
        line_span >= _MAX_PUBLIC_FUNCTION_LINES
        and control_flow.statement_count >= _MAX_TOTAL_STATEMENTS
    ):
        indicators.append("long public function body")
    if control_flow.max_block_statement_count >= _MAX_LINEAR_BLOCK_STATEMENTS:
        indicators.append("large linear statement block")
    return tuple(indicators)


def _symbol_line_span(symbol: PythonSymbol) -> int:
    if symbol.end_line is None:
        return 0
    return max(1, symbol.end_line - symbol.location.line + 1)


def _summary(
    symbol: PythonSymbol,
    control_flow: PythonFunctionControlFlow,
    *,
    line_span: int,
) -> str:
    return (
        f"{symbol.qualified_name} spans {line_span} lines with "
        f"{control_flow.statement_count} statements and a "
        f"{control_flow.max_block_statement_count}-statement linear block."
    )
