"""Provider-owned language and ecosystem knowledge search axes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._semantic_search_common import header, path_hit
from ._semantic_search_knowledge_facts import axis_detail, knowledge_facts
from ._semantic_search_model import PythonSemanticSearchOptions


def knowledge_payload(
    project_root: Path,
    options: PythonSemanticSearchOptions,
) -> dict[str, Any]:
    """Return a semantic-search payload for provider knowledge axes."""

    axis = options.view
    detail = axis_detail(axis)
    query = options.query or ""
    terms = _query_terms(query)
    facts = knowledge_facts(project_root, axis, terms)
    hits = [
        path_hit(
            ".",
            ".",
            kind="text",
            symbol=str(fact["id"]),
            score=2 if terms else 1,
            reason=f"{axis}:{detail['authority']}",
            fields={"axis": axis, "authority": detail["authority"], **fact["fields"]},
        )
        for fact in facts[:12]
    ]
    missing = not facts
    return {
        "header": header(
            axis,
            {
                "q": query,
                "evidenceGrade": "unknown" if missing else "fact",
                "authority": detail["authority"],
                "fact": len(facts),
                "hit": len(hits),
            },
        ),
        "packages": facts,
        "nodes": [
            {
                "id": f"knowledge:{axis}:{fact['id']}",
                "kind": "fact",
                "fields": {"axis": axis, **fact["fields"]},
            }
            for fact in facts
        ],
        "edges": [],
        "owners": [],
        "hits": hits,
        "findings": [],
        "nextActions": [
            {"kind": "lexical", "target": query or axis},
            {"kind": "owner", "target": "."},
        ],
        "notes": [
            {
                "kind": "fact-scope",
                "message": (
                    f"{axis} search did not find a provider-owned fact for the query; "
                    "refine the axis query or route through owner/deps/tree-sitter evidence"
                    if missing
                    else detail["summary"]
                ),
            },
            {"kind": "next-step", "message": detail["next"]},
        ],
    }


def _query_terms(query: str) -> list[str]:
    return [term for term in query.lower().split() if term]
