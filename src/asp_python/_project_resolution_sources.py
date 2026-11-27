"""Resolve package-manager-declared Python source roots and dependencies."""

from __future__ import annotations

import fnmatch
import re
from pathlib import PurePosixPath
from typing import Any

from ._project_resolution_backends import build_backend, package_backend_source_roots


def workspace_manifests(
    root_manifest: PurePosixPath,
    document: dict[str, Any],
    manifests: list[PurePosixPath],
) -> list[PurePosixPath]:
    tool = document.get("tool", {})
    uv = tool.get("uv", {}) if isinstance(tool, dict) else {}
    workspace = uv.get("workspace", {}) if isinstance(uv, dict) else {}
    members = workspace.get("members", []) if isinstance(workspace, dict) else []
    excludes = workspace.get("exclude", []) if isinstance(workspace, dict) else []
    if not isinstance(members, list) or not all(
        isinstance(item, str) for item in members
    ):
        raise ValueError("tool.uv.workspace.members must be an array of strings")
    if not isinstance(excludes, list) or not all(
        isinstance(item, str) for item in excludes
    ):
        raise ValueError("tool.uv.workspace.exclude must be an array of strings")
    selected = {root_manifest}
    base = root_manifest.parent
    for manifest in manifests:
        relative_root = manifest.parent.relative_to(base).as_posix()
        if relative_root == ".":
            continue
        if any(
            fnmatch.fnmatchcase(relative_root, pattern) for pattern in members
        ) and not any(
            fnmatch.fnmatchcase(relative_root, pattern) for pattern in excludes
        ):
            selected.add(manifest)
    return sorted(selected)


def resolved_source_paths(
    document: dict[str, Any],
    package_root: PurePosixPath,
    candidates: list[PurePosixPath],
) -> tuple[list[str], str]:
    roots = _declared_source_roots(document, package_root)
    authority = "manifest-explicit"
    if not roots:
        roots = package_backend_source_roots(document, package_root, candidates)
        authority = "package-manager"
    paths = sorted(
        {
            candidate.as_posix()
            for candidate in candidates
            if candidate.suffix in {".py", ".pyi"}
            and any(candidate == root or root in candidate.parents for root in roots)
        }
    )
    return paths, authority


def _declared_source_roots(
    document: dict[str, Any],
    package_root: PurePosixPath,
) -> set[PurePosixPath]:
    roots: set[PurePosixPath] = set()
    tool = document.get("tool", {})
    if not isinstance(tool, dict):
        tool = {}
    _setuptools_roots(tool.get("setuptools"), package_root, roots)
    _hatch_roots(tool.get("hatch"), package_root, roots)
    _poetry_roots(tool.get("poetry"), package_root, roots)
    _script_roots(document.get("project"), package_root, roots)
    return roots


def _setuptools_roots(
    value: object,
    package_root: PurePosixPath,
    roots: set[PurePosixPath],
) -> None:
    if not isinstance(value, dict):
        return
    package_dir = value.get("package-dir", {})
    if isinstance(package_dir, dict):
        roots.update(
            package_root / item
            for item in package_dir.values()
            if isinstance(item, str)
        )
    find = value.get("packages", {}).get("find", {})
    if isinstance(find, dict):
        where = find.get("where", [])
        if isinstance(where, list):
            roots.update(package_root / item for item in where if isinstance(item, str))
    modules = value.get("py-modules", [])
    if isinstance(modules, list):
        roots.update(
            package_root / (module.replace(".", "/") + ".py")
            for module in modules
            if isinstance(module, str)
        )


def _hatch_roots(
    value: object,
    package_root: PurePosixPath,
    roots: set[PurePosixPath],
) -> None:
    if not isinstance(value, dict):
        return
    wheel = value.get("build", {}).get("targets", {}).get("wheel", {})
    if not isinstance(wheel, dict):
        return
    for key in ("packages", "only-include"):
        entries = wheel.get(key, [])
        if isinstance(entries, list):
            roots.update(
                package_root / item for item in entries if isinstance(item, str)
            )


def _poetry_roots(
    value: object,
    package_root: PurePosixPath,
    roots: set[PurePosixPath],
) -> None:
    if not isinstance(value, dict):
        return
    packages = value.get("packages", [])
    if not isinstance(packages, list):
        return
    for package in packages:
        if not isinstance(package, dict) or not isinstance(package.get("include"), str):
            continue
        source_root = package_root
        if isinstance(package.get("from"), str):
            source_root /= package["from"]
        roots.add(source_root / package["include"])


def _script_roots(
    value: object,
    package_root: PurePosixPath,
    roots: set[PurePosixPath],
) -> None:
    if not isinstance(value, dict):
        return
    for table_name in ("scripts", "gui-scripts"):
        scripts = value.get(table_name, {})
        if not isinstance(scripts, dict):
            continue
        for target in scripts.values():
            if not isinstance(target, str):
                continue
            module = target.split(":", 1)[0].replace(".", "/")
            roots.add(package_root / (module + ".py"))
            roots.add(package_root / module / "__init__.py")


def dependencies_for_manifest(
    packages: list[dict[str, Any]],
    manifest_path: PurePosixPath,
    document: dict[str, Any],
) -> list[dict[str, Any]]:
    package = next(
        (item for item in packages if item["manifestPath"] == manifest_path.as_posix()),
        None,
    )
    if package is None:
        return []
    project = document.get("project", {})
    values = project.get("dependencies", []) if isinstance(project, dict) else []
    if not isinstance(values, list):
        raise ValueError("project.dependencies must be an array")
    return [_dependency(package["packageId"], value) for value in values]


def _dependency(package_id: str, value: object) -> dict[str, Any]:
    if not isinstance(value, str):
        raise ValueError("project.dependencies entries must be strings")
    name_match = re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*", value)
    if name_match is None:
        raise ValueError(f"invalid PEP 508 dependency: {value}")
    name = name_match.group(0)
    return {
        "fromPackageId": package_id,
        "dependencyKey": f"dependencies:{name}",
        "importName": name.replace("-", "_"),
        "packageName": name,
        "kind": "normal",
        "resolution": "external",
        "versionRequirement": value[len(name) :].strip() or "*",
        "optional": False,
        "features": [],
    }


def package_manager(document: dict[str, Any]) -> str:
    tool = document.get("tool", {})
    if isinstance(tool, dict) and isinstance(tool.get("uv"), dict):
        return "uv"
    backend = build_backend(document)
    return backend if backend != "none" else "pep-621"
