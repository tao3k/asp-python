"""Resolve ProjectResolution source roots from Python build-backend semantics."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any


def package_backend_source_roots(
    document: dict[str, Any],
    package_root: PurePosixPath,
    candidates: list[PurePosixPath],
) -> set[PurePosixPath]:
    backend = build_backend(document)
    if backend == "setuptools":
        return _setuptools_default_roots(package_root, candidates)
    if backend in {"hatch", "poetry", "pdm", "flit"}:
        return _named_backend_default_roots(document, package_root, candidates, backend)
    return set()


def build_backend(document: dict[str, Any]) -> str:
    build_system = document.get("build-system", {})
    requires = (
        build_system.get("requires", []) if isinstance(build_system, dict) else []
    )
    joined = (
        " ".join(value for value in requires if isinstance(value, str)).lower()
        if isinstance(requires, list)
        else ""
    )
    for marker, name in (
        ("setuptools", "setuptools"),
        ("hatchling", "hatch"),
        ("poetry-core", "poetry"),
        ("pdm-backend", "pdm"),
        ("flit_core", "flit"),
    ):
        if marker in joined:
            return name
    return "none"


def _setuptools_default_roots(
    package_root: PurePosixPath,
    candidates: list[PurePosixPath],
) -> set[PurePosixPath]:
    src_root = package_root / "src"
    if any(
        candidate.suffix in {".py", ".pyi"} and src_root in candidate.parents
        for candidate in candidates
    ):
        return {src_root}
    excluded = {
        "build",
        "dist",
        "docs",
        "doc",
        "examples",
        "example",
        "tests",
        "test",
        "scripts",
        "tools",
    }
    roots: set[PurePosixPath] = set()
    for candidate in candidates:
        if candidate.suffix not in {".py", ".pyi"}:
            continue
        try:
            relative = candidate.relative_to(package_root)
        except ValueError:
            continue
        if len(relative.parts) == 1:
            roots.add(candidate)
        elif relative.parts[0] not in excluded:
            roots.add(package_root / relative.parts[0])
    return roots


def _named_backend_default_roots(
    document: dict[str, Any],
    package_root: PurePosixPath,
    candidates: list[PurePosixPath],
    backend: str,
) -> set[PurePosixPath]:
    name = _backend_module_name(document, backend)
    if name is None:
        return set()
    module_path = name.replace(".", "/")
    possible = {
        package_root / module_path,
        package_root / (module_path + ".py"),
        package_root / "src" / module_path,
        package_root / "src" / (module_path + ".py"),
    }
    return {
        root
        for root in possible
        if any(
            candidate == root or root in candidate.parents for candidate in candidates
        )
    }


def _backend_module_name(document: dict[str, Any], backend: str) -> str | None:
    tool = document.get("tool", {})
    if not isinstance(tool, dict):
        tool = {}
    if backend == "flit":
        flit = tool.get("flit", {})
        module = flit.get("module", {}) if isinstance(flit, dict) else {}
        if isinstance(module, dict) and isinstance(module.get("name"), str):
            return module["name"]
    project = document.get("project", {})
    name = project.get("name") if isinstance(project, dict) else None
    if not isinstance(name, str) and backend == "poetry":
        poetry = tool.get("poetry", {})
        name = poetry.get("name") if isinstance(poetry, dict) else None
    return re.sub(r"[-.]+", "_", name) if isinstance(name, str) and name else None
