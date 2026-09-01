"""Fast candidate-file pruning for Python semantic lexical search."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ._semantic_search_prefilter_file_scan import (
    python_file_path_matches_by_term,
)
from ._semantic_search_prefilter_path import path_only_term_capped_matches
from ._semantic_search_prefilter_result import (
    MIN_PREFILTER_FILES,
    PythonSearchPrefilterResult,
)
from ._semantic_search_prefilter_select import (
    normalized_terms,
    selected_paths,
    source_matched_files,
    source_only_term_capped_matches,
    term_capped_matches,
)
from ._semantic_search_prefilter_tools import (
    source_match_scores_by_term,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def prefilter_python_text_search_paths(
    project_root: Path,
    query_terms: Sequence[str],
    *,
    owner_path: str | None = None,
) -> PythonSearchPrefilterResult | None:
    """Return parser input files preselected by path and source text."""

    terms = normalized_terms(query_terms)
    rg = shutil.which("rg")
    if not terms and owner_path is None:
        return None
    return _prefilter_with_tools(
        project_root,
        rg,
        terms,
        owner_path=owner_path,
    )


def _prefilter_with_tools(
    project_root: Path,
    rg: str | None,
    terms: tuple[str, ...],
    *,
    owner_path: str | None,
) -> PythonSearchPrefilterResult | None:
    started = time.perf_counter()
    path_match_scan = python_file_path_matches_by_term(
        project_root,
        terms,
        rg=rg,
    )
    path_only_term_capped = path_only_term_capped_matches(
        project_root,
        terms,
        path_match_scan,
    )
    if path_only_term_capped is not None:
        selected = selected_paths(
            project_root,
            path_only_term_capped,
            terms,
            owner_path,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return PythonSearchPrefilterResult(
            paths=selected,
            total_files=path_match_scan.total_files,
            term_capped_files=len(set(path_only_term_capped)),
            matched_files=len(selected),
            elapsed_ms=elapsed_ms,
            tool=path_match_scan.tool,
            reason=(
                f"{path_match_scan.tool} path prefilter selected parser input files "
                "for lexical query"
            ),
            query_terms=len(terms),
            source_search_passes=0,
            file_list_passes=1,
            candidate_file_basis="path-matched-files",
        )

    source_scores_by_term = source_match_scores_by_term(project_root, rg, terms)
    source_tool = "rg" if rg is not None else "rglob-source"
    matched_source_files = source_matched_files(source_scores_by_term)
    source_only_term_capped = source_only_term_capped_matches(
        project_root,
        terms,
        source_scores_by_term,
        matched_source_files,
    )
    if source_only_term_capped is not None:
        selected = selected_paths(
            project_root,
            source_only_term_capped,
            terms,
            owner_path,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return PythonSearchPrefilterResult(
            paths=selected,
            total_files=len(matched_source_files),
            term_capped_files=len(set(source_only_term_capped)),
            matched_files=len(selected),
            elapsed_ms=elapsed_ms,
            tool=source_tool,
            reason=f"{source_tool} source prefilter selected parser input files for lexical query",
            query_terms=len(terms),
            source_search_passes=1 if terms else 0,
            file_list_passes=0,
            candidate_file_basis="source-matched-files",
        )

    if path_match_scan.total_files <= MIN_PREFILTER_FILES:
        return None
    term_capped = term_capped_matches(
        project_root,
        terms,
        path_match_scan.matches_by_term,
        source_scores_by_term,
    )
    selected = selected_paths(project_root, term_capped, terms, owner_path)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    return PythonSearchPrefilterResult(
        paths=selected,
        total_files=path_match_scan.total_files,
        term_capped_files=len(set(term_capped)),
        matched_files=len(selected),
        elapsed_ms=elapsed_ms,
        tool=f"{path_match_scan.tool}+{source_tool}",
        reason=(
            f"{path_match_scan.tool}/{source_tool} prefilter selected parser input "
            "files for lexical query"
        ),
        query_terms=len(terms),
        source_search_passes=1 if terms else 0,
        file_list_passes=1,
        candidate_file_basis="all-python-files",
    )
