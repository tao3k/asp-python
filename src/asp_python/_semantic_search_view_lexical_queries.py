"""Text query-set hit selection helpers for Python semantic search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import dedupe
from ._semantic_search_hits import text_hits
from ._semantic_search_model import MAX_LEXICAL_HITS
from .verification.facts import is_test_path

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport
    from ._semantic_search_model import PythonSemanticSearchOptions


def normalized_query_terms(options: PythonSemanticSearchOptions) -> list[str]:
    if not options.query_set:
        return [] if options.query is None else [options.query]
    return dedupe(term.strip() for term in options.query_set if term.strip())


def lexical_query_hits_by_term(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query_terms: list[str],
    owner_path: str | None,
) -> dict[str, list[dict[str, Any]]]:
    return {
        term: sorted(
            (
                _with_owner_surface(hit)
                for hit in text_hits(report, facts, project_root, term)
                if owner_path is None or hit["ownerPath"] == owner_path
            ),
            key=_text_hit_rank,
        )
        for term in query_terms
    }


def fuzzy_lexical_query_hits_by_term(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query_terms: list[str],
    owner_path: str | None,
) -> dict[str, list[dict[str, Any]]]:
    from ._semantic_search_text_hits import fuzzy_text_hits

    return {
        term: sorted(
            (
                _with_owner_surface(hit)
                for hit in fuzzy_text_hits(report, facts, project_root, term)
                if owner_path is None or hit["ownerPath"] == owner_path
            ),
            key=_text_hit_rank,
        )
        for term in query_terms
    }


def fair_merged_text_hits(
    hits_by_term: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, str, str, str]] = []
    ordered_terms = sorted(
        hits_by_term,
        key=lambda term: (-_term_specificity(term), term.casefold()),
    )
    depth = max((len(hits) for hits in hits_by_term.values()), default=0)
    for depth_index in range(depth):
        _merge_text_hits_at_depth(
            hits_by_term,
            ordered_terms,
            depth_index,
            merged,
            ordered_keys,
        )
    return [merged[key] for key in ordered_keys]


def _merge_text_hits_at_depth(
    hits_by_term: dict[str, list[dict[str, Any]]],
    ordered_terms: list[str],
    depth_index: int,
    merged: dict[tuple[str, str, str, str], dict[str, Any]],
    ordered_keys: list[tuple[str, str, str, str]],
) -> None:
    for term in ordered_terms:
        hits = hits_by_term[term]
        if depth_index < len(hits):
            _merge_text_hit(term, hits[depth_index], merged, ordered_keys)


def _merge_text_hit(
    term: str,
    hit: dict[str, Any],
    merged: dict[tuple[str, str, str, str], dict[str, Any]],
    ordered_keys: list[tuple[str, str, str, str]],
) -> None:
    key = _hit_key(hit)
    current = merged.get(key)
    if current is not None:
        _merge_duplicate_text_hit(term, hit, current)
        return
    if len(ordered_keys) >= MAX_LEXICAL_HITS:
        return
    fields = {**hit.get("fields", {}), "queryTerms": [term]}
    merged[key] = {**hit, "fields": fields}
    ordered_keys.append(key)


def _merge_duplicate_text_hit(
    term: str,
    hit: dict[str, Any],
    current: dict[str, Any],
) -> None:
    fields = dict(current.get("fields", {}))
    fields["queryTerms"] = dedupe([*fields.get("queryTerms", []), term])
    current["fields"] = fields
    current["score"] = max(int(current["score"]), int(hit["score"]))


def _text_hit_rank(hit: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        -int(hit["score"]),
        hit["ownerPath"],
        hit["kind"],
        json.dumps(hit["location"], sort_keys=True),
    )


def _hit_key(hit: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        hit["kind"],
        hit["ownerPath"],
        hit.get("symbol", ""),
        json.dumps(hit["location"], sort_keys=True),
    )


def _term_specificity(term: str) -> int:
    compact = term.strip()
    structural = sum(
        1
        for character in compact
        if character in {".", "_", "/", '"', "'", "(", ")", "[", "]", ":"}
    )
    return len(set(compact.casefold())) + len(compact) + (structural * 8)


def _with_owner_surface(hit: dict[str, Any]) -> dict[str, Any]:
    owner_path = hit["ownerPath"]
    surface = "test-source" if is_test_path(owner_path) else "real-source"
    return {**hit, "surface": surface, "realOwner": True}
