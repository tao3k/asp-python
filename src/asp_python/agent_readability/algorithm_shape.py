"""Agent-facing algorithm-shape advice from parser-owned function facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._agent_policy_catalog import PY_AGENT_R009, agent_policy_rule
from .._model import AspPythonFinding
from ._boundaries import (
    agent_readability_function_is_boundary,
    agent_readability_public_class_scopes,
    agent_readability_report_is_in_scope,
)
from ._software_criteria import (
    CONTROL_FLOW_DECISION_STACK,
    CONTROL_FLOW_LITERAL_DISPATCH_CHAIN,
    CONTROL_FLOW_TRAVERSAL_KNOT,
    finding_labels,
)

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonFunctionControlFlow,
        PythonModuleReport,
        PythonSymbol,
    )


def agent_algorithm_shape_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return machine-readability advice for public algorithm boundaries."""

    if not agent_readability_report_is_in_scope(report):
        return ()
    findings: list[AspPythonFinding] = []
    rule = agent_policy_rule(PY_AGENT_R009)
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
        profile = _agent_algorithm_profile(control_flow)
        if not profile:
            continue
        criterion_ids = _agent_algorithm_software_criteria(profile)
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=_summary(symbol, control_flow),
                location=symbol.location,
                requirement=f"{rule.requirement} Criteria: {', '.join(profile)}.",
                source_line=report.source_line(symbol.location.line),
                label="make this algorithm shape explicit",
                labels=finding_labels(dict(rule.labels), criterion_ids),
            )
        )
    return tuple(findings)


def _agent_algorithm_profile(
    control_flow: PythonFunctionControlFlow,
) -> tuple[str, ...]:
    indicators: list[str] = []
    if control_flow.max_nesting_depth >= 4:
        indicators.append("deep control-flow nesting")
    if control_flow.max_loop_nesting_depth >= 2 and control_flow.branch_count >= 3:
        indicators.append("nested loops mixed with branches")
    if control_flow.max_literal_dispatch_chain >= 4 and control_flow.match_count == 0:
        indicators.append("literal dispatch chain without match/case")
    if control_flow.terminal_else_count >= 2 and control_flow.max_nesting_depth >= 3:
        indicators.append("else blocks after terminal branches")
    if control_flow.nested_control_flow_count >= 4:
        indicators.append("many nested control-flow blocks")
    return tuple(indicators)


def _agent_algorithm_software_criteria(profile: tuple[str, ...]) -> tuple[str, ...]:
    criterion_ids: list[str] = []
    for indicator in profile:
        if indicator in {
            "deep control-flow nesting",
            "else blocks after terminal branches",
            "many nested control-flow blocks",
        }:
            criterion_ids.append(CONTROL_FLOW_DECISION_STACK)
        elif indicator == "nested loops mixed with branches":
            criterion_ids.append(CONTROL_FLOW_TRAVERSAL_KNOT)
        elif indicator == "literal dispatch chain without match/case":
            criterion_ids.append(CONTROL_FLOW_LITERAL_DISPATCH_CHAIN)
    return tuple(dict.fromkeys(criterion_ids))


def _summary(
    symbol: PythonSymbol,
    control_flow: PythonFunctionControlFlow,
) -> str:
    return (
        f"{symbol.qualified_name} has nesting depth "
        f"{control_flow.max_nesting_depth}, loop nesting "
        f"{control_flow.max_loop_nesting_depth}, "
        f"{control_flow.branch_count} branches, and "
        f"literal dispatch chain {control_flow.max_literal_dispatch_chain}."
    )
