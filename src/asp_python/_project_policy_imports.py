"""Project import-name metadata policy backed by parser reasoning facts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser import python_reasoning_tree_facts

from ._model import AspPythonFinding
from ._project_policy_catalog import PY_PROJ_R008, PY_PROJ_R009, project_policy_rule
from ._source import path_location, source_line

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonModuleReport

    from ._model import PythonProjectHarnessScope
    from ._project_metadata import PythonProjectMetadata


def project_import_name_findings(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return findings for declared import names not backed by parser owners."""

    rule = project_policy_rule(PY_PROJ_R008)
    facts = python_reasoning_tree_facts(
        modules,
        import_roots=_reasoning_tree_import_roots(scope, metadata),
        project_root=scope.project_root,
        project_metadata=metadata,
    )
    known_namespaces = {node.namespace for node in facts.nodes if node.namespace}
    findings: list[AspPythonFinding] = []
    findings.extend(_ambiguous_import_name_findings(metadata, pack_id))
    findings.extend(
        _unresolved_entry_point_target_findings(
            metadata,
            known_namespaces=known_namespaces,
            pack_id=pack_id,
        )
    )
    for import_name in metadata.import_names:
        if import_name.name == "" or import_name.namespace in known_namespaces:
            continue
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=(
                    f"{metadata.pyproject_path.name} declares import name "
                    f"{import_name.name!r}, but the parser did not find a "
                    "matching project module owner."
                ),
                location=path_location(metadata.pyproject_path),
                requirement=rule.requirement,
                source_line=source_line(str(metadata.pyproject_path), 1),
                label="align this declared import name with parser-visible code",
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)


def _unresolved_entry_point_target_findings(
    metadata: PythonProjectMetadata,
    *,
    known_namespaces: set[tuple[str, ...]],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    rule = project_policy_rule(PY_PROJ_R009)
    findings: list[AspPythonFinding] = []
    for kind, name, target, target_namespace in _entry_point_targets(metadata):
        if not target_namespace or target_namespace in known_namespaces:
            continue
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=(
                    f"{metadata.pyproject_path.name} declares {kind} "
                    f"{name!r} pointing at {target!r}, but "
                    "the parser did not find that target module."
                ),
                location=path_location(metadata.pyproject_path),
                requirement=rule.requirement,
                source_line=source_line(str(metadata.pyproject_path), 1),
                label="point this entry target at a parser-visible module",
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)


def _entry_point_targets(
    metadata: PythonProjectMetadata,
) -> tuple[tuple[str, str, str, tuple[str, ...]], ...]:
    targets: list[tuple[str, str, str, tuple[str, ...]]] = []
    targets.extend(
        (
            script.kind + " script",
            script.name,
            script.target,
            script.target_namespace,
        )
        for script in (*metadata.scripts, *metadata.gui_scripts)
    )
    targets.extend(
        (
            f"{entry_point.group} entry point",
            entry_point.name,
            entry_point.target,
            entry_point.target_namespace,
        )
        for entry_point in metadata.entry_points
    )
    return tuple(targets)


def _ambiguous_import_name_findings(
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    import_namespaces = {item.name for item in metadata.import_namespaces}
    ambiguous = tuple(
        item
        for item in metadata.import_names
        if item.name != "" and item.name in import_namespaces
    )
    if not ambiguous:
        return ()

    rule = project_policy_rule(PY_PROJ_R008)
    return tuple(
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=(
                f"{metadata.pyproject_path.name} declares {item.name!r} in both "
                "import-names and import-namespaces."
            ),
            location=path_location(metadata.pyproject_path),
            requirement=rule.requirement,
            source_line=source_line(str(metadata.pyproject_path), 1),
            label="keep each import owner in only one metadata table",
            labels=dict(rule.labels),
        )
        for item in ambiguous
    )


def _reasoning_tree_import_roots(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for path in (
        *scope.source_paths,
        *(root.parent for root in metadata.package_roots),
    ):
        _append_path(roots, seen, path)
    if roots:
        return tuple(roots)
    return scope.monitored_paths


def _append_path(paths: list[Path], seen: set[Path], path: Path) -> None:
    key = path.resolve()
    if key in seen:
        return
    seen.add(key)
    paths.append(path)
