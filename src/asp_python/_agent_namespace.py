"""Project-level namespace policy for agent-oriented Python harness runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from python_lang_parser import python_module_namespace_parts

from ._agent_namespace_index import (
    AgentNamespaceItem,
    AgentNamespaceSurface,
    collect_agent_namespace_items,
)
from ._agent_policy_catalog import (
    PY_AGENT_R003,
    PY_AGENT_R004,
    PY_AGENT_R005,
    PY_AGENT_R006,
    agent_policy_rule,
)
from ._model import AspPythonFinding
from ._source import path_location

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonModuleReport

    from ._model import PythonProjectHarnessScope


@dataclass(frozen=True, slots=True)
class _NamespaceConflictSpec:
    surface: AgentNamespaceSurface
    rule_id: str
    label: str
    summary_noun: str


_NAMESPACE_CONFLICT_SPECS = (
    _NamespaceConflictSpec(
        surface=AgentNamespaceSurface.CALLABLE,
        rule_id=PY_AGENT_R003,
        label="rename or namespace this public callable boundary",
        summary_noun="Public symbol",
    ),
    _NamespaceConflictSpec(
        surface=AgentNamespaceSurface.TYPE,
        rule_id=PY_AGENT_R005,
        label="rename or namespace this public type boundary",
        summary_noun="Public symbol",
    ),
    _NamespaceConflictSpec(
        surface=AgentNamespaceSurface.VALUE,
        rule_id=PY_AGENT_R006,
        label="rename or namespace this public value boundary",
        summary_noun="Public value",
    ),
)


def agent_namespace_findings(
    scope: PythonProjectHarnessScope,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return compact project-wide namespace findings for agent repair."""

    findings: list[AspPythonFinding] = []
    namespace_items = collect_agent_namespace_items(modules)
    for spec in _NAMESPACE_CONFLICT_SPECS:
        findings.extend(_duplicate_namespace_findings(namespace_items, spec, pack_id))
    findings.extend(_repeated_namespace_segment_findings(scope, modules, pack_id))
    return tuple(findings)


def _duplicate_namespace_findings(
    namespace_items: tuple[AgentNamespaceItem, ...],
    spec: _NamespaceConflictSpec,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    first_seen: dict[str, AgentNamespaceItem] = {}
    emitted: set[tuple[str, str]] = set()
    findings: list[AspPythonFinding] = []
    rule = agent_policy_rule(spec.rule_id)
    for item in namespace_items:
        if item.surface != spec.surface:
            continue
        first = first_seen.get(item.name)
        if first is None:
            first_seen[item.name] = item
            continue
        key = (item.name, item.module_path or "")
        if key in emitted:
            continue
        emitted.add(key)
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=(
                    f"{spec.summary_noun} {item.name!r} appears in "
                    f"{first.module_name} and {item.module_name}."
                ),
                location=item.location,
                requirement=rule.requirement,
                source_line=item.source_line,
                label=spec.label,
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)


def _repeated_namespace_segment_findings(
    scope: PythonProjectHarnessScope,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    emitted_branches: set[tuple[str, tuple[str, ...]]] = set()
    findings: list[AspPythonFinding] = []
    rule = agent_policy_rule(PY_AGENT_R004)
    for report in modules:
        if not report.path:
            continue
        namespace = python_module_namespace_parts(
            report.path,
            import_roots=scope.monitored_paths,
            project_root=scope.project_root,
        )
        repeated = _first_repeated_namespace_segment(namespace)
        if repeated is None:
            continue
        segment, branch = repeated
        key = (segment, branch)
        if key in emitted_branches:
            continue
        emitted_branches.add(key)
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=f"Module namespace {'.'.join(namespace)!r} repeats {segment!r}.",
                location=path_location(report.path),
                requirement=rule.requirement,
                source_line=report.source_line(1),
                label="rename one repeated namespace segment",
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)


def _first_repeated_namespace_segment(
    namespace: tuple[str, ...],
) -> tuple[str, tuple[str, ...]] | None:
    seen: dict[str, int] = {}
    for index, segment in enumerate(namespace):
        previous_index = seen.setdefault(segment, index)
        if previous_index == index:
            continue
        if _is_src_layout_repeat(namespace, previous_index, index):
            continue
        return segment, namespace[: index + 1]
    return None


def _is_src_layout_repeat(
    namespace: tuple[str, ...],
    previous_index: int,
    index: int,
) -> bool:
    return index == previous_index + 2 and namespace[previous_index + 1] == "src"
