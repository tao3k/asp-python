"""Dependency and import semantic-search views for Python."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import header
from ._semantic_search_deps import (
    dependency_matches,
    dependency_node,
    dependency_query_parts,
    dependency_usage_hits,
    version_scope,
)
from ._semantic_search_hits import import_hits
from ._semantic_search_model import MAX_DEPENDENCY_HITS, MAX_IMPORT_HITS
from ._semantic_search_owners import import_edges, owners_for_paths
from ._semantic_search_packages import dependencies
from ._semantic_search_view_hits import hit_next_actions

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport


def dependency_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
    view: str,
) -> dict[str, Any]:
    """Build dependency/deps payloads."""

    parts = dependency_query_parts(query)
    matches = [
        item
        for item in dependencies(facts)
        if dependency_matches(item, parts["package"])
    ]
    include_usage = bool(parts["apiQuery"])
    usage_hits = (
        dependency_usage_hits(report, project_root, parts["package"])
        if include_usage
        else []
    )
    nodes = [dependency_node(item, parts=parts) for item in matches]
    scope = version_scope(parts, matches)
    hits = usage_hits[:MAX_DEPENDENCY_HITS]
    owners = owners_for_paths(facts, project_root, [hit["ownerPath"] for hit in hits])
    return {
        "header": header(
            view,
            _dependency_header_fields(query, parts, nodes, usage_hits, scope, view),
        ),
        "nodes": nodes[:MAX_DEPENDENCY_HITS],
        "owners": owners,
        "hits": hits,
        "nextActions": _dependency_next_actions(parts, query, hits, scope, view),
        "notes": _dependency_notes(query, nodes, usage_hits, scope, view),
    }


def import_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> dict[str, Any]:
    """Build import edge/search payloads."""

    hits = import_hits(report, project_root, query)[:MAX_IMPORT_HITS]
    edge_matches = _matching_import_edges(facts, project_root, query)
    paths = [hit["ownerPath"] for hit in hits] + _edge_owner_paths(edge_matches)
    return {
        "header": header(
            "import", {"q": query, "edge": len(edge_matches), "hit": len(hits)}
        ),
        "owners": owners_for_paths(facts, project_root, paths),
        "edges": edge_matches,
        "hits": hits,
        "nextActions": hit_next_actions(hits),
        "notes": []
        if edge_matches or hits
        else [{"kind": "not-found", "message": query}],
    }


def _matching_import_edges(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    query_folded = query.casefold()
    return [
        edge
        for edge in import_edges(facts, project_root, limit=MAX_IMPORT_HITS)
        if query_folded in edge["from"].casefold()
        or query_folded in edge["to"].casefold()
        or query_folded in str(edge.get("fields", {}).get("import", "")).casefold()
    ]


def _edge_owner_paths(edges: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for edge in edges:
        paths.extend((edge["from"].removeprefix("O:"), edge["to"].removeprefix("O:")))
    return paths


def _dependency_header_fields(
    query: str,
    parts: dict[str, str],
    nodes: list[dict[str, Any]],
    usage_hits: list[dict[str, Any]],
    scope: str,
    view: str,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "q": query,
        "manifest": len(nodes),
        "usage": len(usage_hits),
        "versionScope": scope,
        "topology": "asp-owned",
    }
    if view == "deps":
        fields.update(
            {
                "dep": 1 if parts["package"] else 0,
                "package": parts["package"],
                "api": parts["apiQuery"],
                "hit": len(nodes) + len(usage_hits),
                "view": "hits",
            }
        )
        if parts["requestedVersion"]:
            fields["requestedVersion"] = parts["requestedVersion"]
    return fields


def _dependency_next_actions(
    parts: dict[str, str],
    query: str,
    hits: list[dict[str, Any]],
    scope: str,
    view: str,
) -> list[dict[str, Any]]:
    package = parts["package"]
    api_query = parts["apiQuery"]
    if view == "deps":
        actions = [
            {"kind": "dependency", "target": package},
            {"kind": "public-external-types", "target": package},
        ]
        if api_query:
            actions.append({"kind": "api", "target": query})
        if api_query and scope == "current":
            actions.extend(
                (
                    {"kind": "text", "target": api_query},
                    {"kind": "tests", "target": api_query},
                )
            )
        return [action for action in actions if action["target"]]
    return [
        *hit_next_actions(hits)[:4],
        {"kind": "public-external-types", "target": package},
        {"kind": "import", "target": query or package},
    ]


def _dependency_notes(
    query: str,
    nodes: list[dict[str, Any]],
    usage_hits: list[dict[str, Any]],
    scope: str,
    view: str,
) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    if not nodes and not usage_hits:
        notes.append({"kind": "not-found", "message": query})
    if view == "deps" and scope == "external":
        notes.append(
            {
                "kind": "fact-scope",
                "message": "requested dependency version is outside the current workspace metadata; local usage is not attributed to that version",
            }
        )
    return notes
