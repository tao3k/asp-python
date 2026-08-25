"""Semantic query-packet field and match construction."""

from __future__ import annotations

from typing import Any

from ._semantic_projection import semantic_query_projection


def semantic_query_match_mode(match: str) -> str:
    """Map owner-item matching detail to the public packet mode."""

    if match in {"exact", "fallback-contains", "candidate"}:
        return match
    return "unknown"


def semantic_query_coverage(
    term: str,
    items: list[dict[str, Any]],
    match: str,
    import_routes: list[Any],
) -> dict[str, Any]:
    """Summarize a single query term against compact owner items."""

    exact_count = sum(1 for item in items if item.get("name") == term)
    if exact_count:
        return {
            "value": term,
            "status": "hit",
            "match": "exact",
            "matchCount": exact_count,
        }
    contains_count = sum(
        1 for item in items if term.casefold() in str(item.get("name", "")).casefold()
    )
    if contains_count and match == "fallback-contains":
        return {
            "value": term,
            "status": "hit",
            "match": "fallback-contains",
            "matchCount": contains_count,
        }
    candidate_routes = _routes_for_term(import_routes, term)
    if candidate_routes:
        return {
            "value": term,
            "status": "partial",
            "match": "candidate",
            "matchCount": len(candidate_routes),
            "candidateNames": [
                f"{route['ownerPath']}::{route['query']}" for route in candidate_routes
            ],
            "nextAction": semantic_import_route_next(candidate_routes[0]),
        }
    return {
        "value": term,
        "status": "miss",
        "match": "none",
        "matchCount": 0,
        "nextAction": "query:broader-owner-item",
    }


def semantic_query_match(
    item: dict[str, Any],
    *,
    include_code: bool,
) -> dict[str, Any]:
    """Render one compact item as its public query-packet match."""

    fields = item.get("fields", {})
    location = item.get("location", {})
    match = {
        "name": item["name"],
        "kind": item["kind"],
        "visibility": "public" if fields.get("public") else "private",
        "doc": bool(fields.get("doc")),
        "location": {"path": location["path"], "lineRange": location["lineRange"]},
        "structuralSelector": fields["structuralSelector"],
        "displayLineRange": fields["displayLineRange"],
        "sourceLocatorHint": fields["sourceLocatorHint"],
        "read": fields["read"],
        "patchSafety": {
            "level": "read-safe",
            "reason": "read exact source locator before editing this compact match",
            "exactRead": fields["read"],
        },
        "truncated": bool(fields.get("truncated")),
        "fields": {
            "public": bool(fields.get("public")),
            "reason": str(fields.get("reason", "item-query")),
        },
    }
    for syntax_key in ("syntaxQueryRef", "syntaxMatchRef", "syntaxCaptureRef"):
        syntax_value = fields.get(syntax_key)
        if isinstance(syntax_value, str):
            match["fields"][syntax_key] = syntax_value
    code = fields.get("code")
    if include_code and isinstance(code, str):
        match["code"] = code
        projection = semantic_query_projection(match, fields, code)
        projected_code = _projected_code_from_rows(projection)
        if projected_code:
            match["code"] = projected_code
        match["projection"] = projection
        match["outline"] = {
            "summary": f"{match['kind']} {match['name']}",
            "hotBlocks": [
                {
                    "label": match["name"],
                    "read": match["read"],
                    "reason": "parser-item-query",
                },
            ],
        }
    return match


def _routes_for_term(import_routes: list[Any], term: str) -> list[dict[str, str]]:
    return [
        route
        for route in import_routes
        if isinstance(route, dict) and route.get("term") == term
    ]


def semantic_import_route_next(route: dict[str, str]) -> str:
    return (
        "asp python search owner "
        f"{route['ownerPath']} items --query {route['query']} --workspace . --view seeds"
    )


def _projected_code_from_rows(projection: dict[str, Any]) -> str:
    rows = projection.get("renderedRows")
    if not isinstance(rows, list):
        return ""
    texts = [
        str(row.get("text", ""))
        for row in rows
        if isinstance(row, dict) and str(row.get("text", "")).strip()
    ]
    return "\n".join(texts)
