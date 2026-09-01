"""Ranking and caps for Python semantic-search prefilter candidates."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

MAX_PREFILTER_FILES_PER_TERM = 2
MAX_PREFILTER_FILES_TOTAL = 6


def path_matches(
    project_root: Path,
    paths: Sequence[Path],
    terms: Sequence[str],
) -> set[Path]:
    """Return files whose owner path matches at least one query term."""

    folded_terms = tuple(term.casefold() for term in terms)
    matches: set[Path] = set()
    for path in paths:
        relative = relative_posix(path, project_root).casefold()
        if any(term in relative for term in folded_terms):
            matches.add(path)
    return matches


def ranked_term_matches(
    _project_root: Path,
    term: str,
    path_match_set: set[str],
    source_scores: dict[str, int],
) -> list[tuple[str, int]]:
    """Return one term's candidates ranked before parser parsing."""

    best_scores = {path: 1 for path in path_match_set}
    for path, score in source_scores.items():
        best_scores[path] = min(best_scores.get(path, score), score)
    return sorted(
        best_scores.items(),
        key=lambda item: (item[1], path_key_rank(item[0], (term,))),
    )


def ranked_capped_matches(
    _project_root: Path,
    paths: Sequence[str],
) -> tuple[str, ...]:
    """Return globally capped candidate paths."""

    return tuple(sorted(set(paths), key=lambda path: path_key_rank(path, ())))[
        :MAX_PREFILTER_FILES_TOTAL
    ]


def path_rank(
    project_root: Path,
    path: Path,
    terms: Sequence[str],
) -> tuple[int, int, int, int, str]:
    """Rank source owners before tests, shallow files, and long paths."""

    relative = relative_posix(path, project_root)
    return path_key_rank(relative, terms)


def path_key_rank(
    relative: str,
    terms: Sequence[str],
) -> tuple[int, int, int, int, str]:
    """Rank project-relative source keys before path objects are needed."""

    folded = relative.casefold()
    folded_terms = tuple(term.casefold() for term in terms)
    return (
        1 if _is_test_path(relative) else 0,
        0 if folded_terms and any(term in folded for term in folded_terms) else 1,
        relative.count("/"),
        len(relative),
        relative,
    )


def relative_posix(path: Path, project_root: Path) -> str:
    """Return a stable path key relative to the search root."""

    root_key = project_root.as_posix().rstrip("/")
    path_key = path.as_posix()
    if path_key == root_key:
        return "."
    prefix = f"{root_key}/"
    if path_key.startswith(prefix):
        return path_key.removeprefix(prefix)
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path_key


def _is_test_path(relative_path: str) -> bool:
    return (
        relative_path == "tests"
        or relative_path.startswith("tests/")
        or "/tests/" in relative_path
        or relative_path.startswith("test_")
        or "/test_" in relative_path
    )
