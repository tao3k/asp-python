"""Rule catalog for native Python syntax and compile diagnostics."""

from __future__ import annotations

from dataclasses import replace

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

from ._model import AspPythonRule

SYNTAX_PACK_ID = "python.syntax"
PYTHON_SYNTAX_INVALID = "python.syntax.invalid"
PYTHON_COMPILE_INVALID = "python.compile.invalid"

_RULE_LABELS = {
    "language": "python",
    "domain": "syntax",
}
_RULES = (
    AspPythonRule(
        rule_id=PYTHON_SYNTAX_INVALID,
        pack_id=SYNTAX_PACK_ID,
        severity=PythonDiagnosticSeverity.ERROR,
        title="Python source did not parse",
        requirement="Python modules must parse with CPython native syntax before project rules run.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PYTHON_COMPILE_INVALID,
        pack_id=SYNTAX_PACK_ID,
        severity=PythonDiagnosticSeverity.ERROR,
        title="Python source did not compile",
        requirement="Python modules must compile through CPython native validation before project rules run.",
        labels=dict(_RULE_LABELS),
    ),
)
_RULE_BY_ID = {rule.rule_id: rule for rule in _RULES}


def python_syntax_rules() -> tuple[AspPythonRule, ...]:
    """Return compact metadata for native Python syntax rules."""

    return tuple(replace(rule, labels=dict(rule.labels)) for rule in _RULES)


def syntax_rule(rule_id: str) -> AspPythonRule:
    """Return one syntax rule descriptor by stable rule id."""

    rule = _RULE_BY_ID.get(rule_id)
    if rule is not None:
        return rule
    return AspPythonRule(
        rule_id=rule_id,
        pack_id=SYNTAX_PACK_ID,
        severity=PythonDiagnosticSeverity.ERROR,
        title="Python parser emitted an error diagnostic",
        requirement=(
            "Python modules must be readable, parseable, and compile through "
            "CPython native validation before project rules run."
        ),
        labels=dict(_RULE_LABELS),
    )
