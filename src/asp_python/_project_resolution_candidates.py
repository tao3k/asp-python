"""Validate ASP-scoped candidates and load only declared project manifests."""

from __future__ import annotations

import tomllib
from pathlib import Path, PurePosixPath
from typing import Any


def candidate_paths_from_entries(entries: list[Any]) -> list[PurePosixPath]:
    paths: list[PurePosixPath] = []
    for entry in entries:
        if not isinstance(entry, str):
            raise ValueError("each ProjectResolution candidate path must be text")
        path = PurePosixPath(entry)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(
                f"ProjectResolution candidate must be scope-relative: {path}"
            )
        paths.append(path)
    return sorted(set(paths))


def candidate_pyproject_paths(
    candidate_paths: list[PurePosixPath],
) -> list[PurePosixPath]:
    return sorted(path for path in candidate_paths if path.name == "pyproject.toml")


def load_pyproject_document(
    workspace_root: Path,
    path: PurePosixPath,
) -> dict[str, Any]:
    return tomllib.loads(_candidate_absolute_path(workspace_root, path).read_text())


def _candidate_absolute_path(root: Path, path: PurePosixPath) -> Path:
    absolute = (root / path.as_posix()).resolve()
    if root != absolute and root not in absolute.parents:
        raise ValueError(f"ProjectResolution candidate escaped scope root: {path}")
    return absolute
