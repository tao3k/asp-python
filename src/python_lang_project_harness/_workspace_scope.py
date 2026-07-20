"""Provider-owned Python package-manager workspace admission."""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path
from typing import Any

from python_lang_parser import (
    PythonPyprojectParseError,
    parse_python_pyproject_document,
)

from ._cli_args import ProtocolArgs

_LOCKFILES = ("uv.lock", "poetry.lock", "pdm.lock", "Pipfile.lock")


def render_workspace_scope(
    args: ProtocolArgs,
    *,
    project_root: Path,
) -> str | None:
    """Return the standalone workspace-scope fast-path when selected."""

    if args.command != "search" or args.view != "workspace-scope":
        return None
    if not args.json:
        raise ValueError("search workspace-scope requires --json")
    return json.dumps(build_workspace_scope(project_root), sort_keys=True) + "\n"


def build_workspace_scope(project_root: Path) -> dict[str, Any]:
    """Resolve Python workspace membership from pyproject and lock anchors."""

    discovery_root = project_root.resolve()
    root_manifest = discovery_root / "pyproject.toml"
    if not root_manifest.is_file():
        raise ValueError(f"workspace scope requires {root_manifest.as_posix()}")

    root_document = _read_pyproject(root_manifest)
    package_roots = _package_roots(discovery_root, root_document)
    packages = [_package_entry(root) for root in package_roots]
    if not packages:
        raise ValueError("workspace scope resolved no Python packages")

    anchors = _anchors(discovery_root, package_roots)
    workspace_name = _project_name(root_document) or discovery_root.name
    packet: dict[str, Any] = {
        "schemaId": "agent.semantic-protocols.semantic-workspace-scope",
        "schemaVersion": "1",
        "workspaceId": f"python:{workspace_name}",
        "languageId": "python",
        "providerId": "py-harness",
        "packageManager": _package_manager(discovery_root, root_document),
        "sourceExtensions": [".py", ".pyi"],
        "discoveryRoot": discovery_root.as_posix(),
        "anchors": anchors,
        "packages": packages,
        "admittedRoots": [entry["root"] for entry in packages],
    }
    packet["fingerprint"] = _json_fingerprint(packet)
    return packet


def _package_roots(project_root: Path, document: dict[str, Any]) -> list[Path]:
    workspace = _uv_workspace(document)
    roots: set[Path] = set()
    if _project_name(document) is not None:
        roots.add(project_root)
    if workspace is None:
        return sorted(roots)

    excluded = _expanded_roots(project_root, workspace.get("exclude", []))
    for root in _expanded_roots(project_root, workspace.get("members", [])):
        if root not in excluded and (root / "pyproject.toml").is_file():
            roots.add(root)
    return sorted(roots)


def _expanded_roots(project_root: Path, patterns: object) -> set[Path]:
    if not isinstance(patterns, list):
        return set()
    roots: set[Path] = set()
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern:
            continue
        absolute_pattern = str(project_root / pattern)
        for match in glob.glob(absolute_pattern, recursive=True):
            candidate = Path(match).resolve()
            roots.add(
                candidate.parent if candidate.name == "pyproject.toml" else candidate
            )
    return roots


def _package_entry(root: Path) -> dict[str, str]:
    manifest = root / "pyproject.toml"
    document = _read_pyproject(manifest)
    name = _project_name(document)
    if name is None:
        raise ValueError(f"Python package manifest has no [project].name: {manifest}")
    root_text = root.resolve().as_posix()
    identity = hashlib.sha256(root_text.encode("utf-8")).hexdigest()[:12]
    return {
        "packageId": f"python:{name}:{identity}",
        "name": name,
        "root": root_text,
        "manifestPath": manifest.resolve().as_posix(),
        "languageId": "python",
    }


def _anchors(project_root: Path, package_roots: list[Path]) -> list[dict[str, str]]:
    paths: dict[Path, str] = {
        (root / "pyproject.toml").resolve(): "pyproject" for root in package_roots
    }
    root_manifest = (project_root / "pyproject.toml").resolve()
    paths[root_manifest] = "pyproject"
    for name in _LOCKFILES:
        lockfile = (project_root / name).resolve()
        if lockfile.is_file():
            paths[lockfile] = "python-lock"
    return [
        {
            "kind": paths[path],
            "path": path.as_posix(),
            "sha256": _file_fingerprint(path),
        }
        for path in sorted(paths)
    ]


def _read_pyproject(path: Path) -> dict[str, Any]:
    try:
        return parse_python_pyproject_document(path)
    except PythonPyprojectParseError as error:
        raise ValueError(str(error)) from error


def _project_name(document: dict[str, Any]) -> str | None:
    project = document.get("project")
    if not isinstance(project, dict):
        return None
    name = project.get("name")
    return name if isinstance(name, str) and name else None


def _uv_workspace(document: dict[str, Any]) -> dict[str, Any] | None:
    tool = document.get("tool")
    uv = tool.get("uv") if isinstance(tool, dict) else None
    workspace = uv.get("workspace") if isinstance(uv, dict) else None
    return workspace if isinstance(workspace, dict) else None


def _package_manager(project_root: Path, document: dict[str, Any]) -> str:
    tool = document.get("tool")
    if (project_root / "uv.lock").is_file() or (
        isinstance(tool, dict) and isinstance(tool.get("uv"), dict)
    ):
        return "uv"
    return "pip"


def _file_fingerprint(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _json_fingerprint(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
