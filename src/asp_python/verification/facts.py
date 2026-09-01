"""Shared parser-fact helpers for Python verification planning."""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser._reasoning_tree import python_reasoning_tree_facts

from .._render import _render_display_path
from .model import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationEvidence,
    PythonVerificationTaskKind,
)

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonProjectDependency,
        PythonReasoningTreeFacts,
        PythonReasoningTreeNode,
    )

    from .._model import AspPythonReport


def verification_reasoning_tree_facts(
    report: AspPythonReport,
) -> PythonReasoningTreeFacts:
    """Return parser-owned reasoning-tree facts for one harness report."""

    scope = report.project_resolution
    return python_reasoning_tree_facts(
        report.modules,
        import_roots=_reasoning_tree_import_roots(report),
        project_root=None if scope is None else scope.project_root,
        project_metadata=None if scope is None else scope.project_metadata,
    )


def verification_project_root(report: AspPythonReport) -> Path:
    """Return the project root represented by a harness report."""

    if report.project_resolution is not None:
        return report.project_resolution.project_root
    if report.root_paths:
        return Path(report.root_paths[0])
    return Path(".")


def node_responsibilities(
    node: PythonReasoningTreeNode,
) -> tuple[PythonOwnerResponsibility, ...]:
    """Return verification responsibilities implied by one parser tree node."""

    responsibilities: list[PythonOwnerResponsibility] = []
    if node.has_public_surface:
        responsibilities.append(PythonOwnerResponsibility.PUBLIC_API)
    if "performance" in node.path or "benchmark" in node.path:
        responsibilities.append(PythonOwnerResponsibility.PERFORMANCE)
    return tuple(responsibilities)


def node_evidence(
    node: PythonReasoningTreeNode,
) -> tuple[PythonVerificationEvidence, ...]:
    """Return compact evidence for one parser tree node."""

    evidence = [
        PythonVerificationEvidence("kind", node.kind),
        PythonVerificationEvidence("effective-lines", str(node.effective_code_lines)),
    ]
    if node.public_names:
        evidence.append(
            PythonVerificationEvidence("public", ",".join(node.public_names[:4]))
        )
    return tuple(evidence)


def entry_point_owner_paths(
    facts: PythonReasoningTreeFacts,
    *,
    project_root: Path,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return parser-visible owners targeted by project entry points."""

    metadata = facts.project_metadata
    if metadata is None:
        return ()
    namespace_paths = {node.namespace: node.path for node in facts.nodes}
    owners: list[tuple[str, tuple[str, ...]]] = []
    for entry in (*metadata.scripts, *metadata.gui_scripts, *metadata.entry_points):
        path = namespace_paths.get(entry.target_namespace)
        if path is None:
            continue
        owners.append(
            (
                _render_display_path(path, project_root=project_root),
                entry.target_namespace,
            )
        )
    return tuple(owners)


def project_metadata_owner_path(
    facts: PythonReasoningTreeFacts,
    *,
    project_root: Path,
) -> str | None:
    """Return the parser-owned display path for project metadata."""

    metadata = facts.project_metadata
    if metadata is None:
        return None
    return _render_display_path(metadata.pyproject_path, project_root=project_root)


def parser_visible_owner_responsibilities(
    facts: PythonReasoningTreeFacts,
    *,
    project_root: Path,
    dependency_signals: Iterable[PythonVerificationDependencySignal] = (),
) -> dict[str, tuple[PythonOwnerResponsibility, ...]]:
    """Return parser-visible owner responsibilities by display path."""

    owner_responsibilities: dict[str, list[PythonOwnerResponsibility]] = {}
    for node in facts.nodes:
        _append_owner_responsibilities(
            owner_responsibilities,
            _render_display_path(node.path, project_root=project_root),
            node_responsibilities(node),
        )
    for path, _namespace in entry_point_owner_paths(facts, project_root=project_root):
        _append_owner_responsibilities(
            owner_responsibilities,
            path,
            (PythonOwnerResponsibility.CLI,),
        )
    metadata = facts.project_metadata
    metadata_path = project_metadata_owner_path(facts, project_root=project_root)
    if metadata is not None and metadata_path is not None:
        if metadata.pytest_options.enables_asp_python or any(
            entry.group == "pytest11" for entry in metadata.entry_points
        ):
            _append_owner_responsibilities(
                owner_responsibilities,
                metadata_path,
                (PythonOwnerResponsibility.PYTEST_GATE,),
            )
        for _dependency, signal in matched_dependency_signals(
            metadata.dependencies,
            dependency_signals,
        ):
            _append_owner_responsibilities(
                owner_responsibilities,
                metadata_path,
                signal.responsibilities,
            )
    return {
        owner_path: tuple(responsibilities)
        for owner_path, responsibilities in owner_responsibilities.items()
    }


def matched_dependency_signals(
    dependencies: Iterable[PythonProjectDependency],
    signals: Iterable[PythonVerificationDependencySignal],
) -> tuple[tuple[PythonProjectDependency, PythonVerificationDependencySignal], ...]:
    """Return dependency facts matched to configured verification signals."""

    signal_by_name = {
        canonical_distribution_name(signal.package_name): signal for signal in signals
    }
    matches: list[
        tuple[PythonProjectDependency, PythonVerificationDependencySignal]
    ] = []
    for dependency in dependencies:
        signal = signal_by_name.get(canonical_distribution_name(dependency.name))
        if signal is None:
            continue
        matches.append((dependency, signal))
    return tuple(matches)


def require_dependency_name(dependency: PythonProjectDependency) -> str:
    """Return the normalized dependency name from parser-owned metadata."""

    return dependency.name


def is_test_path(path: str) -> bool:
    """Return whether a relative path belongs to a test tree."""

    return (
        path == "tests"
        or path.startswith("tests" + os.sep)
        or path.startswith("tests/")
    )


def verification_fingerprint(
    owner_path: str,
    kind: PythonVerificationTaskKind,
    why: str,
    *,
    binding_label: str = "",
    descriptor_label: str = "",
) -> str:
    """Return the deterministic fingerprint for one verification task."""

    digest = hashlib.sha256(
        f"{owner_path}\0{kind.value}\0{why}\0{binding_label}\0{descriptor_label}".encode()
    ).hexdigest()
    return f"pyv:{digest[:16]}"


def canonical_distribution_name(value: str) -> str:
    """Return normalized Python distribution identity."""

    return re.sub(r"[-_.]+", "-", value).lower()


def _append_owner_responsibilities(
    owner_responsibilities: dict[str, list[PythonOwnerResponsibility]],
    owner_path: str,
    responsibilities: Iterable[PythonOwnerResponsibility],
) -> None:
    owner_values = owner_responsibilities.setdefault(owner_path, [])
    for responsibility in responsibilities:
        if responsibility in owner_values:
            continue
        owner_values.append(responsibility)


def _reasoning_tree_import_roots(
    report: AspPythonReport,
) -> tuple[Path | str, ...]:
    if report.project_resolution is None:
        return report.root_paths
    if report.project_resolution.source_paths:
        return report.project_resolution.source_paths
    return report.project_resolution.monitored_paths
