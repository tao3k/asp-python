"""Symbol and API hit builders for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import (
    dedupe_hits,
    location_from_source,
    path_hit,
    semantic_search_display_path,
)
from ._semantic_search_deps import module_owner_path

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts, PythonSymbol

    from ._model import AspPythonReport


def api_hits(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    """Return public export and public symbol hits."""

    query_folded = query.casefold()
    hits = [
        path_hit(
            semantic_search_display_path(node.path, project_root),
            semantic_search_display_path(node.path, project_root),
            kind="api",
            symbol=name,
            score=4,
            reason="public-export",
            fields={"namespace": ".".join(node.namespace)},
        )
        for node in facts.nodes
        for name in node.public_names
        if query_folded in name.casefold()
    ]
    hits.extend(symbol_hits(report, project_root, query, public_only=True))
    return dedupe_hits(hits)


def symbol_hits(
    report: AspPythonReport,
    project_root: Path,
    query: str,
    *,
    public_only: bool = False,
) -> list[dict[str, Any]]:
    """Return parser symbol/export hits."""

    query_folded = query.casefold()
    hits = [
        hit
        for module in report.modules
        for hit in (
            *_module_symbol_hits(
                module,
                project_root,
                query_folded,
                public_only=public_only,
            ),
            *_module_export_hits(module, project_root, query_folded),
        )
    ]
    return dedupe_hits(hits)


def symbol_hit(
    symbol: PythonSymbol,
    owner_path: str,
    project_root: Path,
    *,
    kind: str,
) -> dict[str, Any]:
    """Return one symbol hit."""

    return {
        "kind": kind,
        "ownerPath": owner_path,
        "location": location_from_source(symbol.location, project_root),
        "score": 4,
        "reason": "symbol-name",
        "symbol": symbol.name,
        "fields": {
            "symbolKind": symbol.kind.value,
            "qualified": symbol.qualified_name,
            "public": symbol.is_public,
        },
    }


def _module_symbol_hits(
    module,
    project_root: Path,
    query_folded: str,
    *,
    public_only: bool,
) -> list[dict[str, Any]]:
    owner_path = module_owner_path(module, project_root)
    kind = "api" if public_only else "symbol"
    return [
        symbol_hit(symbol, owner_path, project_root, kind=kind)
        for symbol in module.symbols
        if _symbol_matches(symbol, query_folded, public_only=public_only)
    ]


def _module_export_hits(
    module,
    project_root: Path,
    query_folded: str,
) -> list[dict[str, Any]]:
    owner_path = module_owner_path(module, project_root)
    return [
        path_hit(
            owner_path,
            owner_path,
            kind="export",
            symbol=export_name,
            score=3,
            reason="export-name",
        )
        for export_name in module.export_candidates
        if query_folded in export_name.casefold()
    ]


def _symbol_matches(
    symbol: PythonSymbol,
    query_folded: str,
    *,
    public_only: bool,
) -> bool:
    if public_only and not symbol.is_public:
        return False
    names = (symbol.name, symbol.qualified_name)
    return any(query_folded in name.casefold() for name in names)
