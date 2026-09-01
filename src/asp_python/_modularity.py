"""Python module-shape rule pack for file-level modularity gates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser import (
    PythonDiagnosticSeverity,
    python_reasoning_tree_facts,
    python_symbol_is_callable,
    python_symbol_is_class,
)

from ._model import (
    AspPythonFinding,
    AspPythonRule,
    PythonRulePackDescriptor,
)
from ._modularity_signals import (
    collect_module_complexity_signals,
    module_needs_split,
)
from ._source import path_location

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from python_lang_parser import PythonModuleReport, PythonSymbol

    from ._model import PythonProjectHarnessScope

MODULARITY_PACK_ID = "python.modularity"
PY_MOD_R006 = "PY-MOD-R006"
PY_MOD_R007 = "PY-MOD-R007"

_RULE_LABELS = {
    "language": "python",
    "domain": "modularity",
}
_RULES = (
    AspPythonRule(
        rule_id=PY_MOD_R006,
        pack_id=MODULARITY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Python module appears too large for one ownership seam",
        requirement="Split large multi-responsibility Python modules into focused modules behind an explicit package facade.",
        labels=dict(_RULE_LABELS),
    ),
    AspPythonRule(
        rule_id=PY_MOD_R007,
        pack_id=MODULARITY_PACK_ID,
        severity=PythonDiagnosticSeverity.WARNING,
        title="Python module shadows a package owner",
        requirement="Keep one source owner per import namespace; choose either the module file or the package `__init__.py` owner for this reasoning-tree branch.",
        labels=dict(_RULE_LABELS),
    ),
)
_RULE_BY_ID = {rule.rule_id: rule for rule in _RULES}


@dataclass(frozen=True, slots=True)
class PythonModularityRulePack:
    """Numbered Python modularity rules backed by native parser reports."""

    pack_id: str = MODULARITY_PACK_ID

    def descriptor(self) -> PythonRulePackDescriptor:
        """Return stable metadata for this rule pack."""

        return PythonRulePackDescriptor(
            id=self.pack_id,
            version="v1",
            domains=("modularity", "architecture", "python"),
            default_mode="blocking",
        )

    def evaluate(self, report: PythonModuleReport) -> Iterable[AspPythonFinding]:
        """Evaluate Python module-shape rules for one parsed module report."""

        if not report.is_valid:
            return ()
        return _file_modularity_findings(report, self.pack_id)

    def evaluate_project_modules(
        self,
        scope: PythonProjectHarnessScope,
        modules: Sequence[PythonModuleReport],
    ) -> Iterable[AspPythonFinding]:
        """Evaluate package-tree modularity rules over a parsed project."""

        return _reasoning_tree_findings(scope, modules, self.pack_id)


def python_modularity_rules() -> tuple[AspPythonRule, ...]:
    """Return compact metadata for the default Python modularity rules."""

    return tuple(replace(rule, labels=dict(rule.labels)) for rule in _RULES)


def _file_modularity_findings(
    report: PythonModuleReport,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    shape = report.shape
    if shape is None:
        return ()
    if _is_data_model_catalog(report):
        return ()

    signals = collect_module_complexity_signals(report)
    if not module_needs_split(signals):
        return ()

    rule = _rule(PY_MOD_R006)
    path = Path(report.path or "<memory>")
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=(
                f"{path.name} has {signals.effective_code_lines} effective lines, "
                f"{signals.top_level_statement_count} top-level items, "
                f"{signals.responsibility_group_count} responsibility groups, "
                f"{signals.public_surface_count} public surface items, "
                f"{signals.long_function_count} long functions, "
                f"and max function span {signals.max_function_lines} lines."
            ),
            location=path_location(path),
            requirement=(
                f"Split {path.name} into focused modules because mixed signals "
                f"cross the modularity budget: "
                f"{', '.join(signals.split_indicators)}."
            ),
            source_line=report.source_line(1),
            label="split this module into focused ownership seams",
            labels=dict(rule.labels),
        ),
    )


def _reasoning_tree_findings(
    scope: PythonProjectHarnessScope,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    facts = python_reasoning_tree_facts(
        modules,
        import_roots=_reasoning_tree_import_roots(scope),
        project_root=scope.project_root,
        project_metadata=scope.project_metadata,
    )
    rule = _rule(PY_MOD_R007)
    modules_by_path = {
        module.path: module for module in modules if module.path is not None
    }
    findings: list[AspPythonFinding] = []
    for shadow in facts.shadowed_module_sources:
        package_module = modules_by_path.get(shadow.package_init_path)
        namespace = ".".join(shadow.namespace)
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=(
                    f"{shadow.module_path} and {shadow.package_init_path} "
                    f"both define Python import owner {namespace!r}."
                ),
                location=path_location(shadow.package_init_path),
                requirement=rule.requirement,
                source_line=(
                    None if package_module is None else package_module.source_line(1)
                ),
                label="choose one source owner for this package branch",
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)


def _reasoning_tree_import_roots(scope: PythonProjectHarnessScope) -> tuple[Path, ...]:
    if scope.source_paths:
        return scope.source_paths
    return scope.monitored_paths


def _is_data_model_catalog(report: PythonModuleReport) -> bool:
    top_level_symbols = tuple(symbol for symbol in report.symbols if symbol.scope == "")
    if not top_level_symbols:
        return False
    classes = tuple(
        symbol for symbol in top_level_symbols if python_symbol_is_class(symbol)
    )
    callables = tuple(
        symbol for symbol in top_level_symbols if python_symbol_is_callable(symbol)
    )
    if not classes:
        return False
    if any(not symbol.name.startswith("_") for symbol in callables):
        return False
    return all(_is_data_model_class(symbol) for symbol in classes)


def _is_data_model_class(symbol: PythonSymbol) -> bool:
    if _has_dataclass_decorator(symbol.decorators):
        return True
    return any(_is_data_model_base(base_class) for base_class in symbol.base_classes)


def _has_dataclass_decorator(decorators: tuple[str, ...]) -> bool:
    return any(
        decorator == "dataclass"
        or decorator.startswith("dataclass(")
        or decorator.endswith(".dataclass")
        or ".dataclass(" in decorator
        for decorator in decorators
    )


def _is_data_model_base(base_class: str) -> bool:
    base_name = base_class.rsplit(".", 1)[-1]
    return base_name in {
        "Enum",
        "Flag",
        "IntEnum",
        "IntFlag",
        "Protocol",
        "StrEnum",
    }


def _rule(rule_id: str) -> AspPythonRule:
    return _RULE_BY_ID[rule_id]
