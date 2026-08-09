"""Render deterministic ProjectResolution and package-graph receipts."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT_RESOLUTION_SCHEMA_ID = "agent.semantic-protocols.project-resolution"
PACKAGE_GRAPH_SCHEMA_ID = "agent.semantic-protocols.language-package-graph"


def build_scope_document(
    *,
    parser_id: str,
    workspace_root: Path,
    project_manifest: PurePosixPath,
    selected_manifests: list[PurePosixPath],
    candidate_paths: list[PurePosixPath],
    candidate_generation: dict[str, Any],
    packages: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    scopes: list[dict[str, Any]],
    unresolved: list[dict[str, str]],
    manifest_read_count: int,
) -> dict[str, Any]:
    generation_digest = candidate_generation["digest"]
    package_ids_by_name = {
        package["name"]: package["packageId"] for package in packages
    }
    internal_dependencies = []
    external_dependencies = []
    for dependency in dependencies:
        to_package_id = package_ids_by_name.get(dependency["packageName"])
        if to_package_id is not None:
            internal_dependencies.append(
                {
                    "fromPackageId": dependency["fromPackageId"],
                    "toPackageId": to_package_id,
                    "kind": dependency["kind"],
                }
            )
        else:
            external_dependencies.append(
                {
                    "dependencyId": "python-dependency-"
                    + hashlib.sha256(
                        (
                            dependency["fromPackageId"]
                            + ":"
                            + dependency["packageName"]
                        ).encode()
                    ).hexdigest()[:16],
                    "name": dependency["packageName"],
                    "kind": dependency["kind"],
                    "requested": dependency["versionRequirement"],
                }
            )
    return {
        "schemaId": PROJECT_RESOLUTION_SCHEMA_ID,
        "schemaVersion": "1",
        "state": "resolved",
        "completeness": "exact" if not unresolved else "partial",
        "languageId": "python",
        "providerId": "py-harness",
        "parserId": parser_id,
        "candidateGenerationDigest": generation_digest,
        "projectEntry": project_manifest.as_posix(),
        "packageGraph": {
            "schemaId": PACKAGE_GRAPH_SCHEMA_ID,
            "schemaVersion": "1",
            "languageId": "python",
            "providerId": "py-harness",
            "projectEntry": project_manifest.as_posix(),
            "parserId": parser_id,
            "manifests": [
                _project_file(workspace_root, path, "pyproject-toml")
                for path in selected_manifests
            ],
            "lockfiles": [
                _project_file(workspace_root, path, _lockfile_kind(path))
                for path in candidate_paths
                if path.name in {"uv.lock", "poetry.lock", "pdm.lock"}
            ],
            "packages": packages,
            "internalDependencyEdges": internal_dependencies,
            "externalDependencies": external_dependencies,
            "unresolved": unresolved,
        },
        "sourceScopes": scopes,
        "conflicts": [],
        "metrics": {
            "parsedManifestCount": manifest_read_count,
            "parsedLockfileCount": sum(
                path.name in {"uv.lock", "poetry.lock", "pdm.lock"}
                for path in candidate_paths
            ),
            "affectedPackageCount": len(packages),
            "fullWorkspaceReads": 0,
            "fullManifestReparses": 0,
            "dbOpens": 0,
            "elapsedMicros": 0,
        },
    }


def path_text(path: PurePosixPath) -> str:
    return "." if path.as_posix() == "." else path.as_posix()


def _project_file(root: Path, path: PurePosixPath, kind: str) -> dict[str, str]:
    return {
        "path": path.as_posix(),
        "kind": kind,
        "digest": "sha256:"
        + hashlib.sha256((root / path.as_posix()).read_bytes()).hexdigest(),
    }


def _lockfile_kind(path: PurePosixPath) -> str:
    return {
        "uv.lock": "uv-lock",
        "poetry.lock": "poetry-lock",
        "pdm.lock": "pdm-lock",
    }[path.name]
