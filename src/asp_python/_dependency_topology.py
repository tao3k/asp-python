"""Canonical dependency-topology packets for the ASP provider contract."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from python_lang_parser import parse_python_project_metadata

_REQUIREMENT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
_VERSION_PREFIXES = ("===", "==", "~=", "!=", ">=", "<=", ">", "<")


def build_dependency_topology_packet(project_root: str | Path) -> dict[str, Any]:
    """Build the language-neutral dependency topology consumed by ASP."""

    root = Path(project_root).resolve()
    dependencies = sorted(
        _collect_dependencies(root),
        key=lambda item: (item[0], item[2] != "pyproject.toml", item[2], item[1]),
    )
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    emitted_dependencies: set[str] = set()
    emitted_versions: set[str] = set()

    for name, version, manifest_path in dependencies:
        dependency_id = f"dependency:{name}"
        if dependency_id not in emitted_dependencies:
            nodes.append(
                {
                    "id": dependency_id,
                    "kind": "dependency",
                    "value": name,
                    "path": manifest_path,
                    "fields": {
                        "dependencyName": name,
                        "manifestPath": manifest_path,
                    },
                }
            )
            emitted_dependencies.add(dependency_id)

        if not version or name in emitted_versions:
            continue
        version_id = f"dependency-version:{name}"
        nodes.append(
            {
                "id": version_id,
                "kind": "dependency-version",
                "value": version,
                "fields": {"version": version},
            }
        )
        edges.append(
            {
                "source": dependency_id,
                "target": version_id,
                "relation": "version_locked",
            }
        )
        emitted_versions.add(name)

    graph = {"nodes": nodes, "edges": edges}
    canonical_graph = json.dumps(
        graph,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "packetKind": "dependency-topology",
        "fingerprint": f"sha256:{hashlib.sha256(canonical_graph).hexdigest()}",
        "graph": graph,
    }


def render_dependency_topology_packet(project_root: str | Path) -> str:
    """Render one stable JSON object followed by a newline."""

    return (
        json.dumps(
            build_dependency_topology_packet(project_root),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def _collect_dependencies(root: Path) -> set[tuple[str, str, str]]:
    collected: set[tuple[str, str, str]] = set()
    metadata = parse_python_project_metadata(root)
    if metadata is not None:
        for dependency in metadata.dependencies:
            name = _normalize_dependency_name(dependency.name)
            if not name:
                continue
            collected.add(
                (
                    name,
                    _requirement_version(dependency.requirement, dependency.name),
                    "pyproject.toml",
                )
            )

    for requirements_path in _requirements_paths(root):
        manifest_path = requirements_path.relative_to(root).as_posix()
        for requirement in _requirements(requirements_path):
            collected.add((requirement[0], requirement[1], manifest_path))
    return collected


def _requirements_paths(root: Path) -> tuple[Path, ...]:
    paths = {
        path
        for path in (
            root / "requirements.txt",
            root / "requirements-dev.txt",
            root / "requirements-test.txt",
        )
        if path.is_file()
    }
    requirements_dir = root / "requirements"
    if requirements_dir.is_dir():
        paths.update(path for path in requirements_dir.glob("*.txt") if path.is_file())
    return tuple(sorted(paths))


def _requirements(path: Path) -> Iterable[tuple[str, str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return ()

    requirements: list[tuple[str, str]] = []
    for line in lines:
        parsed = _parse_requirement(line)
        if parsed is not None:
            requirements.append(parsed)
    return tuple(requirements)


def _parse_requirement(line: str) -> tuple[str, str] | None:
    requirement = line.strip()
    if not requirement or requirement.startswith(
        ("#", "-", "git+", "http://", "https://")
    ):
        return None
    requirement = requirement.split(" #", 1)[0].split(";", 1)[0].strip()
    match = _REQUIREMENT_NAME.match(requirement)
    if match is None:
        return None
    name = _normalize_dependency_name(match.group(0))
    remainder = requirement[match.end() :].strip()
    if remainder.startswith("["):
        closing = remainder.find("]")
        remainder = remainder[closing + 1 :].strip() if closing >= 0 else ""
    version = remainder if remainder.startswith(_VERSION_PREFIXES) else ""
    return name, version


def _normalize_dependency_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value.strip().casefold())


def _requirement_version(requirement: str, dependency_name: str) -> str:
    remainder = requirement.strip()
    name_match = _REQUIREMENT_NAME.match(remainder)
    if name_match is not None:
        remainder = remainder[name_match.end() :].strip()
    elif remainder.casefold().startswith(dependency_name.casefold()):
        remainder = remainder[len(dependency_name) :].strip()
    if remainder.startswith("["):
        closing = remainder.find("]")
        remainder = remainder[closing + 1 :].strip() if closing >= 0 else ""
    remainder = remainder.split(";", 1)[0].strip()
    return remainder if remainder.startswith(_VERSION_PREFIXES) else ""
