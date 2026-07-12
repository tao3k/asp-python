"""Text query-set coverage and next-action synthesis helpers."""

from __future__ import annotations

from typing import Any

from ._semantic_search_common import dedupe


def query_coverage(
    hits_by_term: dict[str, list[dict[str, Any]]],
    selected_hits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_counts = _selected_query_term_counts(selected_hits)
    return [
        _query_term_coverage(term, hits, selected_counts.get(term, 0))
        for term, hits in hits_by_term.items()
    ]


def owner_resolution(owner_paths: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "target": owner_path,
            "status": "workspace-owner",
            "realOwner": True,
            "ownerPath": owner_path,
            "reason": "parser-visible owner selected by lexical search",
        }
        for owner_path in owner_paths[:8]
    ]


def search_synthesis(
    query_terms: list[str],
    hits: list[dict[str, Any]],
    owner_paths: list[str],
) -> dict[str, Any] | None:
    if not query_terms:
        return None
    ranked_owners = _rank_synthesis_owners(hits, owner_paths)
    edit_frontier = [
        owner_path
        for owner_path in ranked_owners
        if not _is_test_owner_path(owner_path)
    ][:4]
    test_frontier = [
        owner_path for owner_path in ranked_owners if _is_test_owner_path(owner_path)
    ][:4]
    window_set = [
        *({"kind": "owner", "target": owner_path} for owner_path in edit_frontier),
        *({"kind": "tests", "target": owner_path} for owner_path in test_frontier),
    ][:8]
    return {
        "algorithm": "query-set-owner-resolution",
        "scope": "query-set",
        "summary": (
            f"query-set compressed {len(query_terms)} query terms into "
            f"{len(owner_paths)} parser-visible owners"
        ),
        "selectedOwners": len(ranked_owners),
        **({"editFrontier": edit_frontier} if edit_frontier else {}),
        **({"testFrontier": test_frontier} if test_frontier else {}),
        **({"windowSet": window_set} if window_set else {}),
        "seeds": window_set,
        "fields": {
            "querySet": len(query_terms),
            "owners": len(owner_paths),
            "hits": len(hits),
        },
    }


def avoid_next_actions(
    query_terms: list[str],
    owner_paths: list[str],
) -> list[dict[str, Any]]:
    owner_path_set = set(owner_paths)
    return [
        {
            "kind": "owner",
            "target": term,
            "reason": "query-term-not-parser-visible-owner",
        }
        for term in query_terms
        if _looks_like_project_path(term) and term not in owner_path_set
    ][:8]


def _selected_query_term_counts(
    selected_hits: list[dict[str, Any]],
) -> dict[str, int]:
    selected_counts: dict[str, int] = {}
    for hit in selected_hits:
        for term in hit.get("fields", {}).get("queryTerms", []):
            selected_counts[term] = selected_counts.get(term, 0) + 1
    return selected_counts


def _query_term_coverage(
    term: str,
    hits: list[dict[str, Any]],
    selected_count: int,
) -> dict[str, Any]:
    hit_count = len(hits)
    return {
        "value": term,
        "kind": "text",
        "selector": "exact",
        "status": _coverage_status(hit_count, selected_count),
        "hitCount": hit_count,
        "surfaces": dedupe(hit["surface"] for hit in hits),
        "ownerPaths": dedupe(hit["ownerPath"] for hit in hits)[:8],
        "fields": {"selectedHits": selected_count},
    }


def _coverage_status(hit_count: int, selected_count: int) -> str:
    if hit_count and selected_count < hit_count:
        return "partial"
    if hit_count:
        return "hit"
    return "miss"


def _rank_synthesis_owners(
    hits: list[dict[str, Any]],
    owner_paths: list[str],
) -> list[str]:
    term_counts: dict[str, set[str]] = {owner_path: set() for owner_path in owner_paths}
    best_scores: dict[str, int] = {owner_path: 0 for owner_path in owner_paths}
    for hit in hits:
        owner_path = hit["ownerPath"]
        term_counts.setdefault(owner_path, set()).update(
            hit.get("fields", {}).get("queryTerms", [])
        )
        best_scores[owner_path] = max(best_scores.get(owner_path, 0), int(hit["score"]))
    return sorted(
        owner_paths,
        key=lambda owner_path: (
            -len(term_counts.get(owner_path, set())),
            -best_scores.get(owner_path, 0),
            owner_path,
        ),
    )


def _is_test_owner_path(owner_path: str) -> bool:
    return (
        owner_path.startswith("tests/")
        or owner_path.startswith("test/")
        or "/tests/" in owner_path
        or "/test/" in owner_path
        or "/__tests__/" in owner_path
        or owner_path.endswith("_test.py")
        or owner_path.endswith("_test.pyi")
        or owner_path.endswith(".test.py")
        or owner_path.endswith(".spec.py")
    )


def _looks_like_project_path(term: str) -> bool:
    return (
        "/" in term
        and " " not in term
        and "\\" not in term
        and ":" not in term
        and not term.startswith("/")
        and all(part not in {"", ".", ".."} for part in term.split("/"))
    )
