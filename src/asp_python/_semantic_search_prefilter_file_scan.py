"""Python file-list scanning for semantic-search prefilters."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._constants import IGNORED_DIR_NAMES, INCLUDE_HIDDEN_DIR_NAMES
from ._semantic_search_prefilter_process import run_prefilter_command

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class PythonFilePathMatchScan:
    """A single file-list pass with path matches grouped by query term."""

    total_files: int
    matches_by_term: dict[str, set[str]]
    tool: str


def list_python_files(
    project_root: Path,
    *,
    ignored_dir_names: frozenset[str] = IGNORED_DIR_NAMES,
    include_hidden_dir_names: frozenset[str] = INCLUDE_HIDDEN_DIR_NAMES,
) -> tuple[Path, ...]:
    """Return scannable Python files below a project root."""

    fd = shutil.which("fd") or shutil.which("fdfind")
    if fd is not None:
        process = run_prefilter_command(
            _fd_python_files_command(fd, ignored_dir_names),
            cwd=project_root,
        )
        if process.returncode == 0:
            return trusted_tool_paths_from_output(project_root, process.stdout)
    return tuple(
        sorted(
            (
                path.resolve()
                for path in project_root.rglob("*.py")
                if not _ignored(
                    path, project_root, ignored_dir_names, include_hidden_dir_names
                )
            ),
            key=lambda path: path.as_posix(),
        )
    )


def python_file_path_matches_by_term(
    project_root: Path,
    terms: Sequence[str],
    *,
    rg: str | None = None,
    ignored_dir_names: frozenset[str] = IGNORED_DIR_NAMES,
    include_hidden_dir_names: frozenset[str] = INCLUDE_HIDDEN_DIR_NAMES,
) -> PythonFilePathMatchScan:
    """Return Python file counts and path matches from one file-list pass."""

    normalized_terms = tuple(dict.fromkeys(term for term in terms if term))
    if rg is not None:
        process = run_prefilter_command(
            _rg_python_files_command(rg, ignored_dir_names),
            cwd=project_root,
        )
        if process.returncode == 0:
            return _path_match_scan_from_output(
                project_root,
                process.stdout,
                normalized_terms,
                tool="rg",
            )
    fd = shutil.which("fd") or shutil.which("fdfind")
    if fd is not None:
        process = run_prefilter_command(
            _fd_python_files_command(fd, ignored_dir_names),
            cwd=project_root,
        )
        if process.returncode == 0:
            return _path_match_scan_from_output(
                project_root,
                process.stdout,
                normalized_terms,
                tool="fd+rg",
            )
    return _path_match_scan_from_rglob(
        project_root,
        normalized_terms,
        ignored_dir_names=ignored_dir_names,
        include_hidden_dir_names=include_hidden_dir_names,
    )


def paths_from_output(project_root: Path, stdout: str) -> tuple[Path, ...]:
    """Return existing Python files named by command output."""

    paths: list[Path] = []
    for line in stdout.splitlines():
        if not line:
            continue
        path = Path(line)
        if not path.is_absolute():
            path = project_root / path
        resolved = path.resolve()
        if resolved.is_file() and resolved.suffix == ".py":
            paths.append(resolved)
    return tuple(sorted(set(paths), key=lambda path: path.as_posix()))


def trusted_tool_paths_from_output(project_root: Path, stdout: str) -> tuple[Path, ...]:
    """Return Python files from a trusted fd/rg file-list command."""

    paths = [
        path if path.is_absolute() else project_root / path
        for line in stdout.splitlines()
        if line
        for path in (Path(line),)
    ]
    return tuple(sorted(set(paths), key=lambda path: path.as_posix()))


def _path_match_scan_from_output(
    project_root: Path,
    stdout: str,
    terms: Sequence[str],
    *,
    tool: str,
) -> PythonFilePathMatchScan:
    folded_terms = tuple((term, term.casefold()) for term in terms)
    matches_by_term: dict[str, set[str]] = {term: set() for term in terms}
    total_files = 0
    for line in stdout.splitlines():
        if not line:
            continue
        total_files += 1
        for term, folded_term in folded_terms:
            if _path_contains_term(line, folded_term):
                matches_by_term[term].add(line)
    return PythonFilePathMatchScan(
        total_files=total_files,
        matches_by_term=matches_by_term,
        tool=tool,
    )


def _path_match_scan_from_rglob(
    project_root: Path,
    terms: Sequence[str],
    *,
    ignored_dir_names: frozenset[str],
    include_hidden_dir_names: frozenset[str],
) -> PythonFilePathMatchScan:
    folded_terms = tuple((term, term.casefold()) for term in terms)
    matches_by_term: dict[str, set[str]] = {term: set() for term in terms}
    total_files = 0
    for path in project_root.rglob("*.py"):
        if _ignored(path, project_root, ignored_dir_names, include_hidden_dir_names):
            continue
        total_files += 1
        relative = path.relative_to(project_root).as_posix()
        for term, folded_term in folded_terms:
            if _path_contains_term(relative, folded_term):
                matches_by_term[term].add(relative)
    return PythonFilePathMatchScan(
        total_files=total_files,
        matches_by_term=matches_by_term,
        tool="rglob",
    )


def _path_contains_term(path: str, folded_term: str) -> bool:
    folded_path = path.casefold()
    if folded_term in folded_path:
        return True
    compact_term = _compact_path_token(folded_term)
    return len(compact_term) >= 3 and compact_term in _compact_path_token(folded_path)


def _compact_path_token(value: str) -> str:
    return "".join(char for char in value if char.isalnum())


def _fd_python_files_command(fd: str, ignored_dir_names: frozenset[str]) -> list[str]:
    return [
        fd,
        "--color",
        "never",
        "-t",
        "f",
        "-e",
        "py",
        *(_fd_excludes(ignored_dir_names)),
        ".",
        ".",
    ]


def _rg_python_files_command(rg: str, ignored_dir_names: frozenset[str]) -> list[str]:
    return [
        rg,
        "--color",
        "never",
        "--files",
        "--glob",
        "*.py",
        *(_rg_excludes(ignored_dir_names)),
        ".",
    ]


def _fd_excludes(ignored_dir_names: frozenset[str]) -> tuple[str, ...]:
    args: list[str] = []
    for name in sorted(ignored_dir_names):
        args.extend(("-E", name))
    return tuple(args)


def _rg_excludes(ignored_dir_names: frozenset[str]) -> tuple[str, ...]:
    args: list[str] = []
    for name in sorted(ignored_dir_names):
        args.extend(("--glob", f"!{name}/**"))
    return tuple(args)


def _ignored(
    path: Path,
    project_root: Path,
    ignored_dir_names: frozenset[str],
    include_hidden_dir_names: frozenset[str],
) -> bool:
    return any(
        part in ignored_dir_names
        or (
            part.startswith(".")
            and part not in {".", ".."}
            and part not in include_hidden_dir_names
        )
        for part in path.relative_to(project_root).parts
    )
