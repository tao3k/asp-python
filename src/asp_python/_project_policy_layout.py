"""Project metadata and package-root layout policy helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._model import AspPythonFinding
from ._project_policy_catalog import PY_PROJ_R001, PY_PROJ_R002, project_policy_rule
from ._source import path_location, source_line

if TYPE_CHECKING:
    from pathlib import Path

    from ._model import PythonProjectHarnessScope
    from ._project_metadata import PythonProjectMetadata


def project_layout_findings(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return findings for project source and package-root layout."""

    if not _is_packaged_project(metadata):
        return ()

    return (
        *_src_layout_findings(scope, metadata, pack_id),
        *_declared_package_root_findings(metadata, pack_id),
    )


def _is_packaged_project(metadata: PythonProjectMetadata) -> bool:
    return (
        metadata.has_project_table
        or metadata.has_build_system_table
        or bool(metadata.package_roots)
    )


def _src_layout_findings(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    if _uses_src_layout(scope, metadata):
        return ()

    rule = project_policy_rule(PY_PROJ_R001)
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=f"{metadata.pyproject_path.name} is present but project sources are not under src/.",
            location=path_location(metadata.pyproject_path),
            requirement=rule.requirement,
            source_line=source_line(str(metadata.pyproject_path), 1),
            label="declare package code under src/",
            labels=dict(rule.labels),
        ),
    )


def _uses_src_layout(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
) -> bool:
    src_roots = _src_layout_roots(scope, metadata)
    if not src_roots:
        return False
    if not metadata.package_roots:
        return True
    return all(
        any(_is_relative_to(package_root, src_root) for src_root in src_roots)
        for package_root in metadata.package_roots
    )


def _src_layout_roots(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
) -> tuple[Path, ...]:
    src_roots: list[Path] = []
    root_src = metadata.project_root / "src"
    if root_src in scope.source_paths:
        src_roots.append(root_src)
    for package_root in metadata.package_roots:
        src_parent = _src_parent_for_package(package_root, metadata.project_root)
        if src_parent is not None and src_parent not in src_roots:
            src_roots.append(src_parent)
    return tuple(src_roots)


def _src_parent_for_package(package_root: Path, project_root: Path) -> Path | None:
    if not _is_relative_to(package_root, project_root):
        return None
    for parent in package_root.parents:
        if parent == project_root:
            break
        if parent.name == "src":
            return parent
    return None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _declared_package_root_findings(
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    findings: list[AspPythonFinding] = []
    rule = project_policy_rule(PY_PROJ_R002)
    for package_root in metadata.package_roots:
        init_file = package_root / "__init__.py"
        if package_root.is_dir() and init_file.is_file():
            continue
        finding_path = (
            package_root if package_root.exists() else metadata.pyproject_path
        )
        findings.append(
            AspPythonFinding(
                rule_id=rule.rule_id,
                pack_id=pack_id,
                severity=rule.severity,
                title=rule.title,
                summary=f"Declared wheel package root {package_root} is not an importable package directory.",
                location=path_location(finding_path),
                requirement=rule.requirement,
                source_line=source_line(str(finding_path), 1),
                label="make this declared package root importable",
                labels=dict(rule.labels),
            )
        )
    return tuple(findings)
