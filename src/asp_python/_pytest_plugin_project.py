"""Project-scope resolution for the pytest integration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from python_lang_parser._pyproject_metadata import parse_python_project_metadata

if TYPE_CHECKING:
    from collections.abc import Sequence


def project_root(config: pytest.Config) -> Path:
    """Resolve the configured or uniquely targeted Python project root."""

    configured_root = config.getoption("--python-project-harness-root")
    if configured_root:
        return Path(configured_root)
    root = Path(config.rootpath)
    return (
        _package_scoped_root(
            root,
            config.invocation_params.args,
            invocation_dir=Path(config.invocation_params.dir),
        )
        or root
    )


def _package_scoped_root(
    pytest_root: Path,
    args: Sequence[str],
    *,
    invocation_dir: Path,
) -> Path | None:
    """Find one package root when pytest targets exactly one Python project."""

    candidates: list[Path] = []
    for raw_arg in args:
        if raw_arg.startswith("-"):
            continue
        raw_path = raw_arg.split("::", 1)[0]
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = invocation_dir / path
        path = path.resolve()
        if not path.exists():
            return None
        candidate = _nearest_python_project(path, pytest_root.resolve())
        if candidate is None:
            return None
        candidates.append(candidate)

    if not candidates or any(
        candidate != candidates[0] for candidate in candidates[1:]
    ):
        return None
    candidate = candidates[0]
    if candidate == pytest_root.resolve():
        return None
    return candidate


def _nearest_python_project(path: Path, pytest_root: Path) -> Path | None:
    """Return the nearest real Python project containing ``path``."""

    start = path if path.is_dir() else path.parent
    for candidate in (start, *start.parents):
        if not _is_relative_to(candidate, pytest_root):
            break
        metadata = parse_python_project_metadata(candidate)
        if metadata is not None and (
            metadata.has_project_table or metadata.has_build_system_table
        ):
            return candidate
        if candidate == pytest_root:
            break
    return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
