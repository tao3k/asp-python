"""Agent-facing data/type shape advice from parser-owned class facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_parser import python_symbol_is_public_class

from .._agent_policy_catalog import PY_AGENT_R012, agent_policy_rule
from .._model import AspPythonFinding
from ._boundaries import agent_readability_report_is_in_scope

if TYPE_CHECKING:
    from python_lang_parser import PythonClassShape, PythonModuleReport, PythonSymbol


def agent_type_shape_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return repair advice for public classes that hide data shape."""

    if not agent_readability_report_is_in_scope(report):
        return ()
    rule = agent_policy_rule(PY_AGENT_R012)
    return tuple(
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=_summary(symbol),
            location=symbol.location,
            requirement=f"{rule.requirement} Signals: {_signals(symbol.class_shape)}.",
            source_line=report.source_line(symbol.location.line),
            label="replace manual field storage with a visible data/type anchor",
            labels=dict(rule.labels),
        )
        for symbol in report.symbols
        if _class_needs_visual_anchor(symbol)
    )


def _class_needs_visual_anchor(symbol: PythonSymbol) -> bool:
    class_shape = symbol.class_shape
    return (
        python_symbol_is_public_class(symbol)
        and class_shape is not None
        and class_shape.is_manual_data_carrier
    )


def _summary(symbol: PythonSymbol) -> str:
    class_shape = _known_class_shape(symbol.class_shape)
    return (
        f"{symbol.qualified_name} stores {class_shape.instance_field_count} "
        "instance fields in __init__ without a visible data/type anchor."
    )


def _signals(class_shape: PythonClassShape | None) -> str:
    shape = _known_class_shape(class_shape)
    return (
        f"instance fields={shape.instance_field_count}, "
        f"annotated fields={shape.annotated_field_count}, "
        f"public methods={shape.public_method_count}"
    )


def _known_class_shape(class_shape: PythonClassShape | None) -> PythonClassShape:
    if class_shape is None:  # pragma: no cover - guarded by callers.
        raise ValueError("expected parser class shape facts")
    return class_shape
