"""Rule catalog for modern Python project-shape policy."""

from __future__ import annotations

from dataclasses import replace

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

from ._model import AspPythonRule

PROJECT_POLICY_PACK_ID = "python.project_policy"
PY_PROJ_R001 = "PY-AGENT-PROJECT-001"
PY_PROJ_R002 = "PY-AGENT-PROJECT-002"
PY_PROJ_R003 = "PY-AGENT-PROJECT-003"
PY_PROJ_R004 = "PY-AGENT-PROJECT-004"
PY_PROJ_R005 = "PY-AGENT-PROJECT-005"
PY_PROJ_R006 = "PY-AGENT-PROJECT-006"
PY_PROJ_R007 = "PY-AGENT-PROJECT-007"
PY_PROJ_R008 = "PY-AGENT-PROJECT-008"
PY_PROJ_R009 = "PY-AGENT-PROJECT-009"
PY_PROJ_R010 = "PY-AGENT-PROJECT-010"
PY_PROJ_R011 = "PY-AGENT-PROJECT-011"

_RULE_LABELS = {
    "language": "python",
    "domain": "project-policy",
}
_RULES = (
    AspPythonRule(
        rule_id=PY_PROJ_R001,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Python project should use src layout",
        requirement="Use a `src/` source layout so package imports resolve through the installed project shape instead of the repository root.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R002,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Declared wheel package root is not importable",
        requirement="Ensure each declared wheel package root exists and contains `__init__.py` so agents can map project metadata to import namespaces.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R003,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Typed public package lacks py.typed marker",
        requirement="Add `py.typed` to declared package roots that expose public parser surface so downstream agents and type checkers can trust inline types.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R004,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Typed package public callable lacks annotations",
        requirement="Annotate public callable boundaries in `py.typed` packages so the declared typed surface remains complete and agent-readable.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R005,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Project metadata should declare package name",
        requirement="Declare `[project].name` in `pyproject.toml` so package identity is explicit for build tools, agents, and release metadata.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R006,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Project metadata should declare supported Python versions",
        requirement="Declare `[project].requires-python` so installers, CI, and agents can resolve the intended supported Python range.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R007,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Build-system table should declare build requirements",
        requirement="Declare `[build-system].requires` whenever `[build-system]` is present so isolated builds can install backend requirements deterministically.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R008,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Declared import names should resolve to project modules",
        requirement="Keep `[project].import-names` and `[project].import-namespaces` aligned with parser-visible project owners so agents can trust package scope metadata.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R009,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Declared entry point targets should resolve to project modules",
        requirement="Keep console scripts, GUI scripts, and entry points pointed at parser-visible project modules so agent entry maps and packaging metadata agree.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R010,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Harness dev dependency should mount a pytest gate",
        requirement="Enable `--python-project-harness` in pytest addopts or expose `asp_python_test()` so the dev dependency actually gates project policy.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_PROJ_R011,
        pack_id=PROJECT_POLICY_PACK_ID,
        severity=PythonDiagnosticSeverity.INFO,
        title="Verification profile hints are not configured",
        requirement="Configure `[tool.asp-python.verification].profile_hints` from parser-suggested owners or consume the dependency API verification-profile projection.",
        labels=dict(_RULE_LABELS),
    ),
)
_RULE_BY_ID = {rule.rule_id: rule for rule in _RULES}


def python_project_policy_rules() -> tuple[AspPythonRule, ...]:
    """Return compact metadata for default project-shape rules."""

    return tuple(replace(rule, labels=dict(rule.labels)) for rule in _RULES)


def project_policy_rule(rule_id: str) -> AspPythonRule:
    """Return one project-policy rule descriptor by stable rule id."""

    return _RULE_BY_ID[rule_id]
