"""Candidate selection helpers for Python semantic-search prefilters."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._semantic_search_prefilter_rank import (
    MAX_PREFILTER_FILES_PER_TERM,
    path_key_rank,
    ranked_capped_matches,
    ranked_term_matches,
)
from ._semantic_search_prefilter_result import MIN_PREFILTER_FILES

if TYPE_CHECKING:
    from collections.abc import Sequence


def normalized_terms(query_terms: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(term.strip() for term in query_terms if term.strip()))


def source_only_term_capped_matches(
    project_root: Path,
    terms: tuple[str, ...],
    source_scores_by_term: dict[str, dict[str, int]],
    source_matched_files: frozenset[str],
) -> tuple[str, ...] | None:
    if not _source_only_prefilter_is_sufficient(
        terms,
        source_scores_by_term,
        source_matched_files,
    ):
        return None
    matched: list[str] = []
    for term in terms:
        term_matches = ranked_term_matches(
            project_root,
            term,
            set(),
            source_scores_by_term.get(term, {}),
        )
        matched.extend(
            path for path, _score in term_matches[:MAX_PREFILTER_FILES_PER_TERM]
        )
    return tuple(matched)


def term_capped_matches(
    project_root: Path,
    terms: tuple[str, ...],
    path_matches_by_term: dict[str, set[str]],
    source_scores_by_term: dict[str, dict[str, int]],
) -> tuple[str, ...]:
    matched: list[str] = []
    for term in terms:
        term_matches = ranked_term_matches(
            project_root,
            term,
            path_matches_by_term.get(term, set()),
            source_scores_by_term.get(term, {}),
        )
        matched.extend(
            path for path, _score in term_matches[:MAX_PREFILTER_FILES_PER_TERM]
        )
    return tuple(matched)


def selected_paths(
    project_root: Path,
    term_capped: tuple[str, ...],
    terms: tuple[str, ...],
    owner_path: str | None,
) -> tuple[Path, ...]:
    matched = ranked_capped_matches(project_root, term_capped)
    if owner_path is not None:
        owner_candidate = (project_root / owner_path).resolve()
        if owner_candidate.is_file() and owner_candidate.suffix == ".py":
            matched = (*matched, owner_path)
    return tuple(
        project_root / path
        for path in sorted(set(matched), key=lambda path: path_key_rank(path, terms))
    )


def source_matched_files(
    source_scores_by_term: dict[str, dict[str, int]],
) -> frozenset[str]:
    return frozenset(
        path
        for source_scores in source_scores_by_term.values()
        for path in source_scores
    )


def _source_only_prefilter_is_sufficient(
    terms: tuple[str, ...],
    source_scores_by_term: dict[str, dict[str, int]],
    source_matched_files: frozenset[str],
) -> bool:
    return (
        bool(terms)
        and len(source_matched_files) > MIN_PREFILTER_FILES
        and all(
            len(source_scores_by_term.get(term, {})) >= MAX_PREFILTER_FILES_PER_TERM
            for term in terms
        )
    )
