"""Filesystem-backed candidate discovery for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from ._constants import IGNORED_DIR_NAMES
from ._semantic_search_prefilter_file_scan import list_python_files
from ._semantic_search_prefilter_process import run_prefilter_command


def source_match_scores(
    project_root: Path, rg: str | None, term: str
) -> dict[str, int]:
    """Return candidate files scored by parser-likely source hits."""

    return source_match_scores_by_term(project_root, rg, (term,)).get(term, {})


def source_match_scores_by_term(
    project_root: Path,
    rg: str | None,
    terms: Sequence[str],
    *,
    ignored_dir_names: frozenset[str] = IGNORED_DIR_NAMES,
) -> dict[str, dict[str, int]]:
    """Return source-hit scores for all query terms using one rg scan."""

    normalized_terms = tuple(dict.fromkeys(term for term in terms if term))
    if not normalized_terms:
        return {}
    folded_terms = tuple((term, term.casefold()) for term in normalized_terms)
    if rg is None:
        return _source_match_scores_by_term_rglob(
            project_root,
            folded_terms,
            ignored_dir_names,
        )
    process = run_prefilter_command(
        _rg_source_command(rg, normalized_terms, ignored_dir_names),
        cwd=project_root,
    )
    if process.returncode not in {0, 1}:
        return {}
    scores_by_term: dict[str, dict[str, int]] = {term: {} for term in normalized_terms}
    for line in process.stdout.splitlines():
        _merge_source_line_scores(
            scores_by_term,
            project_root,
            line,
            folded_terms,
        )
    return scores_by_term


def _source_match_scores_by_term_rglob(
    project_root: Path,
    folded_terms: Sequence[tuple[str, str]],
    ignored_dir_names: frozenset[str],
) -> dict[str, dict[str, int]]:
    scores_by_term: dict[str, dict[str, int]] = {
        term: {} for term, _folded_term in folded_terms
    }
    for path in list_python_files(project_root, ignored_dir_names=ignored_dir_names):
        relative = path.relative_to(project_root).as_posix()
        _merge_source_file_scores(scores_by_term, relative, path, folded_terms)
    return scores_by_term


def _merge_source_file_scores(
    scores_by_term: dict[str, dict[str, int]],
    relative_path: str,
    path: Path,
    folded_terms: Sequence[tuple[str, str]],
) -> None:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as source_file:
            for source in source_file:
                for term, folded_term in _matching_terms(source, folded_terms):
                    term_scores = scores_by_term[term]
                    score = _source_line_score(source, folded_term)
                    term_scores[relative_path] = min(
                        term_scores.get(relative_path, score),
                        score,
                    )
    except OSError:
        return


def _merge_source_line_scores(
    scores_by_term: dict[str, dict[str, int]],
    project_root: Path,
    line: str,
    folded_terms: Sequence[tuple[str, str]],
) -> None:
    parsed = _python_source_line(project_root, line)
    if parsed is None:
        return
    resolved, source = parsed
    for term, folded_term in _matching_terms(source, folded_terms):
        term_scores = scores_by_term[term]
        score = _source_line_score(source, folded_term)
        term_scores[resolved] = min(term_scores.get(resolved, score), score)


def _python_source_line(_project_root: Path, line: str) -> tuple[str, str] | None:
    path, source = _split_rg_line(line)
    if path is None:
        return None
    if not path.endswith(".py"):
        return None
    return path, source


def _matching_terms(
    source: str,
    folded_terms: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    folded_source = source.casefold()
    return tuple(
        (term, folded_term)
        for term, folded_term in folded_terms
        if folded_term in folded_source
    )


def _rg_source_command(
    rg: str,
    terms: Sequence[str],
    ignored_dir_names: frozenset[str],
) -> list[str]:
    expressions: list[str] = []
    for term in terms:
        expressions.extend(("-e", term))
    return [
        rg,
        "--color",
        "never",
        "-i",
        "-F",
        "-n",
        "--max-count",
        "50",
        "--glob",
        "*.py",
        *(_rg_excludes(ignored_dir_names)),
        *expressions,
        ".",
    ]


def _rg_excludes(ignored_dir_names: frozenset[str]) -> tuple[str, ...]:
    args: list[str] = []
    for name in sorted(ignored_dir_names):
        args.extend(("--glob", f"!{name}/**"))
    return tuple(args)


def _split_rg_line(line: str) -> tuple[str | None, str]:
    first = line.find(":")
    if first == -1:
        return None, ""
    second = line.find(":", first + 1)
    if second == -1:
        return None, ""
    return line[:first], line[second + 1 :]


def _source_line_score(source_line: str, folded_term: str) -> int:
    stripped = source_line.lstrip()
    folded = stripped.casefold()
    if _starts_with_definition(folded, folded_term):
        return 0
    if folded.startswith(folded_term) and folded[
        len(folded_term) :
    ].lstrip().startswith("="):
        return 1
    if "__all__" in source_line:
        return 2
    return 3


def _starts_with_definition(folded_source_line: str, folded_term: str) -> bool:
    for prefix in ("class ", "def "):
        if not folded_source_line.startswith(prefix):
            continue
        name_start = len(prefix)
        if not folded_source_line.startswith(folded_term, name_start):
            continue
        name_end = name_start + len(folded_term)
        return name_end >= len(folded_source_line) or not _is_identifier_character(
            folded_source_line[name_end]
        )
    return False


def _is_identifier_character(character: str) -> bool:
    return character == "_" or character.isalnum()
