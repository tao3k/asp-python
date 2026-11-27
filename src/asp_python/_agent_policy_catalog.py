"""Rule catalog for agent-oriented Python project policy."""

from __future__ import annotations

from dataclasses import replace

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

from ._model import AspPythonRule

AGENT_POLICY_PACK_ID = "python.agent_policy"
PY_AGENT_R001 = "PY-AGENT-POLICY-001"
PY_AGENT_R002 = "PY-AGENT-POLICY-002"
PY_AGENT_R003 = "PY-AGENT-POLICY-003"
PY_AGENT_R004 = "PY-AGENT-POLICY-004"
PY_AGENT_R005 = "PY-AGENT-POLICY-005"
PY_AGENT_R006 = "PY-AGENT-POLICY-006"
PY_AGENT_R007 = "PY-AGENT-POLICY-007"
PY_AGENT_R008 = "PY-AGENT-POLICY-008"
PY_AGENT_R009 = "PY-AGENT-POLICY-009"
PY_AGENT_R010 = "PY-AGENT-POLICY-010"
PY_AGENT_R011 = "PY-AGENT-POLICY-011"
PY_AGENT_R012 = "PY-AGENT-POLICY-012"

_RULE_LABELS = {
    "language": "python",
    "domain": "agent-policy",
}
_RULES = (
    AspPythonRule(
        rule_id=PY_AGENT_R001,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Library module lacks a module intent docstring",
        requirement="Add a concise module docstring that names the module responsibility for agent search and repair.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R002,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Public callable lacks type annotations",
        requirement="Annotate public function and method boundaries so agents can reason from native syntax without guessing shapes.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R003,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Public callable name conflicts across namespaces",
        requirement="Give project-level public callables unambiguous names or move them behind a clear domain namespace so agents can resolve intent without guessing.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R004,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Module namespace repeats a path segment",
        requirement="Keep Python module namespaces branch-unique; rename repeated path segments so agents see one clear ownership path.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R005,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Public type name conflicts across namespaces",
        requirement="Give project-level public classes unambiguous type names or move them behind a clear domain namespace so agents can resolve intent without guessing.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R006,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Public value name conflicts across namespaces",
        requirement="Give project-level public values and configuration exports unambiguous names or move them behind a clear domain namespace so agents can resolve intent without guessing.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R007,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Branch package lacks reasoning-tree intent docstring",
        requirement="Add a concise package docstring to branch `__init__.py` files so agents can choose the right owner subtree before editing.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R008,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Branch package owns a broad mixed surface",
        requirement="Split crowded branch packages into focused subpackages, or document the facade and owner map so agents do not treat one folder as one responsibility.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R009,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Function hides algorithm behind nested control flow",
        requirement="Flatten deeply nested if/loop logic into guard clauses, explicit dispatch, match/case, or small named pipeline steps so agents can reason about the algorithm shape.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R010,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Function owns a broad linear algorithm surface",
        requirement="Split long public functions with broad linear statement blocks into small named helpers or pipeline steps so agents can edit one algorithm responsibility at a time.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R011,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Function manually spells a native Python transform",
        requirement="Use comprehensions, generator expressions, built-ins such as sum/any/all, collections.Counter/defaultdict, or named iterator pipeline helpers when a loop only maps, filters, counts, groups, accumulates, or answers a predicate.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_AGENT_R012,
        pack_id=AGENT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Class hides data shape behind manual storage",
        requirement="Use a visible data/type anchor such as @dataclass(frozen=True, slots=True), TypedDict, Protocol, Enum/StrEnum, or a named model base when a public class mainly stores fields.",
        labels=dict(_RULE_LABELS),
    ),
)
_RULE_BY_ID = {rule.rule_id: rule for rule in _RULES}


def python_agent_policy_rules() -> tuple[AspPythonRule, ...]:
    """Return compact metadata for the default agent-oriented policy rules."""

    return tuple(replace(rule, labels=dict(rule.labels)) for rule in _RULES)


def agent_policy_rule(rule_id: str) -> AspPythonRule:
    """Return one agent-policy rule descriptor by stable rule id."""

    return _RULE_BY_ID[rule_id]
