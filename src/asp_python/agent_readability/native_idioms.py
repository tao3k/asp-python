"""Agent-facing native-idiom advice from parser-owned function facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._agent_policy_catalog import PY_AGENT_R011, agent_policy_rule
from .._model import AspPythonFinding
from ._boundaries import (
    agent_readability_function_is_boundary,
    agent_readability_public_class_scopes,
    agent_readability_report_is_in_scope,
)
from ._software_criteria import NATIVE_IDIOM_MANUAL_TRANSFORM_LOOP, finding_labels

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonFunctionControlFlow,
        PythonModuleReport,
        PythonSymbol,
    )


def agent_native_idiom_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return repair advice for public functions that miss native Python idioms."""

    if not agent_readability_report_is_in_scope(report):
        return ()
    findings: list[AspPythonFinding] = []
    rule = agent_policy_rule(PY_AGENT_R011)
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
        profile = _native_idiom_profile(control_flow)
        if not profile:
            continue
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
                label="replace this boilerplate loop with a native Python idiom",
                labels=finding_labels(
                    dict(rule.labels),
                    (NATIVE_IDIOM_MANUAL_TRANSFORM_LOOP,),
                ),
            )
        )
    return tuple(findings)


def _native_idiom_profile(
    control_flow: PythonFunctionControlFlow,
) -> tuple[str, ...]:
    indicators: list[str] = []
    if control_flow.manual_collection_loop_count:
        indicators.append("manual collection accumulator loop")
    if control_flow.manual_predicate_loop_count:
        indicators.append("manual predicate loop")
    if control_flow.manual_mapping_count_loop_count:
        indicators.append("manual mapping counter loop")
    if control_flow.manual_mapping_group_loop_count:
        indicators.append("manual mapping grouping loop")
    if control_flow.manual_numeric_sum_loop_count:
        indicators.append("manual numeric sum loop")
    return tuple(indicators)


def _summary(
    symbol: PythonSymbol,
    control_flow: PythonFunctionControlFlow,
) -> str:
    return (
        f"{symbol.qualified_name} has "
        f"{control_flow.manual_collection_loop_count} manual collection loops "
        f"{control_flow.manual_predicate_loop_count} manual predicate loops, "
        f"{control_flow.manual_mapping_count_loop_count} manual counter loops, "
        f"{control_flow.manual_mapping_group_loop_count} manual grouping loops, "
        f"and {control_flow.manual_numeric_sum_loop_count} manual sum loops."
    )
