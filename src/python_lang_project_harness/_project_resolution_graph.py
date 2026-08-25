"""Build Python package graphs from ASP-scoped candidates and pyproject data."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ._project_resolution_candidates import (
    candidate_paths_from_entries,
    candidate_pyproject_paths,
    load_pyproject_document,
)
from ._project_resolution_document import build_scope_document, path_text
from ._project_resolution_sources import (
    dependencies_for_manifest,
    resolved_source_paths,
    workspace_manifests,
)

PARSER_ID = "python.pyproject-toml"


@dataclass(frozen=True)
class ProjectResolutionError(ValueError):
    message: str
    reason_kind: str
    next_action: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class _ProjectResolutionContext:
    candidate_paths: list[PurePosixPath]
    documents: dict[PurePosixPath, dict[str, Any]]
    project_manifest: PurePosixPath
    selected_manifests: list[PurePosixPath]


def resolve_project_resolution(
    request: dict[str, Any],
    *,
    cwd: Path,
) -> dict[str, Any]:
    context = _resolution_context(request, cwd=cwd)
    packages = [
        package
        for path in context.selected_manifests
        if (
            package := _package_from_manifest(
                path,
                context.documents[path],
                context.candidate_paths,
            )
        )
        is not None
    ]
    unresolved, scopes = _scopes(packages)
    dependencies = [
        dependency
        for path in context.selected_manifests
        for dependency in dependencies_for_manifest(
            packages,
            path,
            context.documents[path],
        )
    ]
    return build_scope_document(
        parser_id=PARSER_ID,
        workspace_root=cwd.resolve(),
        project_manifest=context.project_manifest,
        selected_manifests=context.selected_manifests,
        candidate_paths=context.candidate_paths,
        candidate_generation=request["candidateGeneration"],
        packages=packages,
        dependencies=dependencies,
        scopes=scopes,
        unresolved=unresolved,
        manifest_read_count=len(context.documents),
    )


def _resolution_context(
    request: dict[str, Any],
    *,
    cwd: Path,
) -> _ProjectResolutionContext:
    workspace_root = cwd.resolve()
    candidates = candidate_paths_from_entries(request["candidatePaths"])
    root_manifest = PurePosixPath("pyproject.toml")
    manifests = candidate_pyproject_paths(candidates)
    if not manifests:
        raise ProjectResolutionError(
            "provider has no tracked pyproject.toml candidate",
            reason_kind="provider-not-applicable",
            next_action="continue-without-python-provider",
        )
    if root_manifest not in manifests:
        raise ProjectResolutionError(
            "provider project entry is required: candidate pyproject.toml",
            reason_kind="project-entry-missing",
            next_action="include a tracked pyproject.toml repository candidate",
        )
    root_document = load_pyproject_document(workspace_root, root_manifest)
    selected = workspace_manifests(root_manifest, root_document, manifests)
    documents = {
        path: (
            root_document
            if path == root_manifest
            else load_pyproject_document(workspace_root, path)
        )
        for path in selected
    }
    return _ProjectResolutionContext(candidates, documents, root_manifest, selected)


def _package_from_manifest(
    manifest_path: PurePosixPath,
    document: dict[str, Any],
    candidates: list[PurePosixPath],
) -> dict[str, Any] | None:
    project = document.get("project")
    tool = document.get("tool", {})
    uv = tool.get("uv", {}) if isinstance(tool, dict) else {}
    if isinstance(uv, dict) and uv.get("package") is False:
        return None
    poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
    name = project.get("name") if isinstance(project, dict) else None
    if not isinstance(name, str) and isinstance(poetry, dict):
        name = poetry.get("name")
    if not isinstance(name, str) or not name:
        return None
    package_id = (
        "python-package-"
        + hashlib.sha256(f"{manifest_path.as_posix()}:{name}".encode()).hexdigest()[:16]
    )
    source_paths, include_authority = resolved_source_paths(
        document, manifest_path.parent, candidates
    )
    source_roots = sorted(
        {path_text(PurePosixPath(source_path).parent) for source_path in source_paths}
    )
    target_id = (
        "python-target-"
        + hashlib.sha256(f"{package_id}:library".encode()).hexdigest()[:16]
    )
    return {
        "packageId": package_id,
        "name": name,
        **(
            {"version": project["version"]}
            if isinstance(project, dict) and isinstance(project.get("version"), str)
            else {}
        ),
        "root": path_text(manifest_path.parent),
        "manifestPath": manifest_path.as_posix(),
        "workspaceMember": True,
        "targets": [
            {
                "targetId": target_id,
                "name": name,
                "kind": "library",
                "explicit": include_authority == "manifest-explicit",
                "sourceRoots": source_roots,
                "entrypoints": [],
                "generatedRoots": [],
            }
        ],
    }


def _scopes(
    packages: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    unresolved: list[dict[str, str]] = []
    scopes: list[dict[str, Any]] = []
    for package in packages:
        target = package["targets"][0]
        if target["sourceRoots"]:
            scopes.append(
                {
                    "scopeId": "python-source-scope-"
                    + hashlib.sha256(
                        f"{package['packageId']}:{target['targetId']}".encode()
                    ).hexdigest()[:16],
                    "packageId": package["packageId"],
                    "targetId": target["targetId"],
                    "roots": target["sourceRoots"],
                    "explicitPaths": (
                        target["sourceRoots"] if target["explicit"] else []
                    ),
                    "extensions": [".py", ".pyi"],
                    "includeAuthority": (
                        "manifest-explicit" if target["explicit"] else "package-manager"
                    ),
                    "exclusions": [],
                    "classifications": ["production"],
                }
            )
        else:
            unresolved.append(
                {
                    "state": "target-source-missing",
                    "path": package["manifestPath"],
                    "reasonKind": "package-source-scope-missing",
                }
            )
    return unresolved, scopes
