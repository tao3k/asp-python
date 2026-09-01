"""Path-only candidate pruning for Python semantic-search prefilters."""

from __future__ import annotations

from pathlib import Path

from ._semantic_search_prefilter_file_scan import PythonFilePathMatchScan
from ._semantic_search_prefilter_rank import ranked_term_matches


def path_only_term_capped_matches(
    project_root: Path,
    terms: tuple[str, ...],
    path_match_scan: PythonFilePathMatchScan,
) -> tuple[str, ...] | None:
    """Return path-ranked matches when every query term appears in owner paths."""

    if not terms or not all(
        path_match_scan.matches_by_term.get(term) for term in terms
    ):
        return None
    matched: list[str] = []
    for term in terms:
        term_matches = ranked_term_matches(
            project_root,
            term,
            path_match_scan.matches_by_term.get(term, set()),
            {},
        )
        matched.extend(path for path, _score in term_matches)
    return tuple(matched)
