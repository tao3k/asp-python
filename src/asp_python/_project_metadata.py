"""Harness adapter for parser-owned Python project metadata."""

from __future__ import annotations

from pathlib import Path

from python_lang_parser import PythonProjectMetadata, parse_python_project_metadata


def read_python_project_metadata(
    project_root: str | Path,
) -> PythonProjectMetadata | None:
    """Read parser-owned project metadata from `pyproject.toml` when present."""

    return parse_python_project_metadata(project_root)


__all__ = [
    "PythonProjectMetadata",
    "read_python_project_metadata",
]
