"""Project metadata policy helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._model import AspPythonFinding
from ._project_policy_catalog import (
    PY_PROJ_R005,
    PY_PROJ_R006,
    PY_PROJ_R007,
    project_policy_rule,
)
from ._source import path_location, source_line

if TYPE_CHECKING:
    from ._project_metadata import PythonProjectMetadata


def project_metadata_findings(
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return findings for deterministic pyproject metadata contracts."""

    findings: list[AspPythonFinding] = []
    findings.extend(_project_name_findings(metadata, pack_id))
    findings.extend(_requires_python_findings(metadata, pack_id))
    findings.extend(_build_requires_findings(metadata, pack_id))
    return tuple(findings)


def _project_name_findings(
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    if not metadata.has_project_table or metadata.project_name is not None:
        return ()

    rule = project_policy_rule(PY_PROJ_R005)
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=f"{metadata.pyproject_path.name} has [project] metadata without a package name.",
            location=path_location(metadata.pyproject_path),
            requirement=rule.requirement,
            source_line=source_line(str(metadata.pyproject_path), 1),
            label="declare [project].name",
            labels=dict(rule.labels),
        ),
    )


def _requires_python_findings(
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    if not metadata.has_project_table or metadata.requires_python is not None:
        return ()

    rule = project_policy_rule(PY_PROJ_R006)
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=f"{metadata.pyproject_path.name} has [project] metadata without requires-python.",
            location=path_location(metadata.pyproject_path),
            requirement=rule.requirement,
            source_line=source_line(str(metadata.pyproject_path), 1),
            label="declare [project].requires-python",
            labels=dict(rule.labels),
        ),
    )


def _build_requires_findings(
    metadata: PythonProjectMetadata,
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    if not metadata.has_build_system_table or metadata.build_requires:
        return ()

    rule = project_policy_rule(PY_PROJ_R007)
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=f"{metadata.pyproject_path.name} has [build-system] metadata without requires.",
            location=path_location(metadata.pyproject_path),
            requirement=rule.requirement,
            source_line=source_line(str(metadata.pyproject_path), 1),
            label="declare [build-system].requires",
            labels=dict(rule.labels),
        ),
    )
