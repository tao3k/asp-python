"""Text hit builders for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import (
    dedupe_hits,
    location,
    path_hit,
    semantic_search_display_path,
)
from ._semantic_search_deps import module_owner_path
from ._semantic_search_symbol_hits import symbol_hits

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport


def text_hits(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    """Return owner path, export, symbol, and source-line text hits."""

    if not query:
        return []
    query_folded = query.casefold()
    hits = [
        hit
        for node in facts.nodes
        for hit in _node_text_hits(node, project_root, query_folded)
    ]
    hits.extend(symbol_hits(report, project_root, query))
    hits.extend(
        hit
        for module in report.modules
        for hit in _module_source_line_hits(module, project_root, query_folded)
    )
    return dedupe_hits(hits)


def fuzzy_text_hits(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    """Return owner path, export, symbol, and source-line fuzzy hits."""
    if not query:
        return []
    query_folded = query.casefold()
    hits = [
        hit
        for node in facts.nodes
        for hit in _node_fuzzy_text_hits(node, project_root, query_folded)
    ]
    hits.extend(symbol_hits(report, project_root, query))
    hits.extend(
        hit
        for module in report.modules
        for hit in _module_fuzzy_source_line_hits(module, project_root, query_folded)
    )
    return dedupe_hits(hits)


def _node_text_hits(
    node, project_root: Path, query_folded: str
) -> list[dict[str, Any]]:
    owner_path = semantic_search_display_path(node.path, project_root)
    hits = _node_path_hits(node, owner_path, query_folded)
    hits.extend(
        path_hit(
            owner_path,
            owner_path,
            kind="export",
            symbol=export_name,
            score=4,
            reason="export-name",
        )
        for export_name in node.public_names
        if query_folded in export_name.casefold()
    )
    return hits


def _node_fuzzy_text_hits(
    node, project_root: Path, query_folded: str
) -> list[dict[str, Any]]:
    owner_path = semantic_search_display_path(node.path, project_root)
    hits = _node_fuzzy_path_hits(node, owner_path, query_folded)
    export_hits = []
    for export_name in node.public_names:
        score = _fuzzy_score(export_name, query_folded)
        if score is None:
            continue
        export_hits.append(
            path_hit(
                owner_path,
                owner_path,
                kind="export",
                symbol=export_name,
                score=score,
                reason="export-name-fuzzy",
            )
        )
    hits.extend(sorted(export_hits, key=lambda hit: -hit["score"])[:6])
    return hits


def _node_path_hits(node, owner_path: str, query_folded: str) -> list[dict[str, Any]]:
    namespace = ".".join(node.namespace)
    if (
        query_folded not in owner_path.casefold()
        and query_folded not in namespace.casefold()
    ):
        return []
    return [path_hit(owner_path, owner_path, score=3, reason="owner-path")]


def _node_fuzzy_path_hits(
    node, owner_path: str, query_folded: str
) -> list[dict[str, Any]]:
    namespace = ".".join(node.namespace)
    score = max(
        _fuzzy_score(owner_path, query_folded) or 0,
        _fuzzy_score(namespace, query_folded) or 0,
    )
    if score == 0:
        return []
    return [path_hit(owner_path, owner_path, score=score, reason="owner-path-fuzzy")]


def _module_source_line_hits(
    module,
    project_root: Path,
    query_folded: str,
) -> list[dict[str, Any]]:
    owner_path = module_owner_path(module, project_root)
    return [
        {
            "kind": "text",
            "ownerPath": owner_path,
            "location": location(owner_path, line_number),
            "score": 2,
            "reason": "source-text",
            "snippet": source_line.strip()[:160],
            "fields": {"source": "parser-visible-source"},
        }
        for line_number, source_line in enumerate(module.source_lines, start=1)
        if query_folded in source_line.casefold()
    ]


def _module_fuzzy_source_line_hits(
    module,
    project_root: Path,
    query_folded: str,
) -> list[dict[str, Any]]:
    owner_path = module_owner_path(module, project_root)
    hits: list[dict[str, Any]] = []
    for line_number, source_line in enumerate(module.source_lines, start=1):
        score = _fuzzy_score(source_line, query_folded)
        if score is None:
            continue
        hits.append(
            {
                "kind": "text",
                "ownerPath": owner_path,
                "location": location(owner_path, line_number),
                "score": score,
                "reason": "source-text-fuzzy",
                "snippet": source_line.strip()[:160],
                "fields": {"source": "parser-visible-source", "matchMode": "fuzzy"},
            }
        )
    return hits


def _fuzzy_score(candidate: str, query_folded: str) -> int | None:
    query = "".join(query_folded.casefold().split())
    if not query:
        return None
    candidate_folded = candidate.casefold()
    exact_index = candidate_folded.find(query)
    if exact_index >= 0:
        return 12 + len(query)
    positions: list[int] = []
    cursor = 0
    for char in query:
        index = candidate_folded.find(char, cursor)
        if index < 0:
            return None
        positions.append(index)
        cursor = index + len(char)
    if not positions:
        return None
    span = positions[-1] - positions[0] + 1
    if span > max(len(query) * 3, len(query) + 12):
        return None
    compactness = max(0, len(positions) * 2 - (span - len(positions)))
    return 4 + compactness
