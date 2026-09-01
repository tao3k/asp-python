"""Callsite hit builders for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import dedupe_hits, location_from_source
from ._semantic_search_deps import module_owner_path

if TYPE_CHECKING:
    from python_lang_parser import PythonCall

    from ._model import AspPythonReport


def callsite_hits(
    report: AspPythonReport,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    """Return parser-owned Python callsite hits."""

    query_folded = query.casefold()
    hits = [
        callsite_hit(call, module_owner_path(module, project_root), project_root)
        for module in report.modules
        for call in module.calls
        if _call_matches(call, query_folded)
    ]
    return dedupe_hits(hits)


def callsite_hit(
    call: PythonCall,
    owner_path: str,
    project_root: Path,
) -> dict[str, Any]:
    """Return one callsite hit."""

    fields: dict[str, Any] = {
        "scope": call.scope or "module",
        "effect": call.effect.value,
        "positional": call.positional_count,
    }
    if call.keyword_names:
        fields["keywords"] = list(call.keyword_names)
    if call.expression:
        fields["expr"] = call.expression
    return {
        "kind": "callsite",
        "ownerPath": owner_path,
        "location": location_from_source(call.location, project_root),
        "score": _callsite_score(call),
        "reason": "call-expression",
        "symbol": call.function,
        "fields": fields,
    }


def _call_matches(call: PythonCall, query_folded: str) -> bool:
    if not query_folded:
        return False
    haystacks = (call.function, call.function.rsplit(".", 1)[-1])
    return any(query_folded in item.casefold() for item in haystacks if item)


def _callsite_score(call: PythonCall) -> int:
    if "." not in call.function:
        return 4
    return 3
