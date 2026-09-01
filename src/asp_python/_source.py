"""Shared file-location helpers for deterministic harness rules."""

from __future__ import annotations

from os import PathLike
from pathlib import Path

from python_lang_parser import SourceLocation


def path_location(path: str | PathLike[str]) -> SourceLocation:
    """Return the first-token location for a file-level finding."""

    return SourceLocation(path=str(Path(path)), line=1, column=0)


def source_line(path: str | None, line: int) -> str | None:
    """Return one source line for compact diagnostic rendering."""

    if path is None or line < 1:
        return None
    try:
        return Path(path).read_text(encoding="utf-8").splitlines()[line - 1]
    except (OSError, IndexError, UnicodeDecodeError):
        return None
