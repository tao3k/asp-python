"""Workspace package and dependency facts for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import semantic_search_display_path
from ._semantic_search_model import MAX_WORKSPACE_PACKAGES
from .verification.facts import is_test_path

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport


def project_name(facts: PythonReasoningTreeFacts) -> str:
    """Return the project package name used in packet headers."""

    metadata = facts.project_metadata
    if metadata is None or metadata.project_name is None:
        return "python-project"
    return metadata.project_name


def dependencies(facts: PythonReasoningTreeFacts):
    """Return parser-owned project dependency declarations."""

    metadata = facts.project_metadata
    return () if metadata is None else metadata.dependencies


def workspace_packages(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    owner_count: int,
) -> list[dict[str, Any]]:
    """Return ranked workspace package/root facts."""

    metadata = facts.project_metadata
    packages: list[dict[str, Any]] = [
        {
            "id": ".",
            "fields": {
                "name": project_name(facts),
                "role": "workspace-root",
                "packages": owner_count,
                "dependencies": len(dependencies(facts)),
                "next": ["prime:."],
            },
        }
    ]
    roots = () if metadata is None else metadata.package_roots
    for path in roots:
        shown = semantic_search_display_path(path, project_root)
        packages.append(_workspace_package(shown, name=Path(shown).name))
    if len(packages) == 1 and report.project_resolution is not None:
        packages.extend(
            _workspace_package(
                semantic_search_display_path(path, project_root), name=path.name
            )
            for path in report.project_resolution.source_paths
        )
    return _dedupe_packages(packages)[:MAX_WORKSPACE_PACKAGES]


def _workspace_package(path: str, *, name: str) -> dict[str, Any]:
    return {
        "id": path,
        "fields": {
            "name": name,
            "role": "workspace-package",
            "surface": _workspace_package_surface(path),
            "next": [f"prime:{path}"],
        },
    }


def _workspace_package_surface(path: str) -> str:
    if is_test_path(path):
        return "test"
    if path == "docs" or path.startswith("docs/"):
        return "docs"
    if path == "examples" or path.startswith(("examples/", "demo/", "demos/")):
        return "demo"
    return "source"


def _dedupe_packages(packages: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for package in packages:
        if package["id"] in seen:
            continue
        seen.add(package["id"])
        result.append(package)
    return sorted(
        result,
        key=lambda package: (
            0 if package["id"] == "." else 1,
            package["id"].count("/"),
            package["id"],
        ),
    )
