"""Stdin ingest semantic-search view for Python."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import header
from ._semantic_search_ingest import ingest_hits
from ._semantic_search_model import MAX_LEXICAL_HITS
from ._semantic_search_owners import owners_for_paths
from ._semantic_search_view_actions import hit_next_actions

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts


def ingest_payload(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    stdin: str,
) -> dict[str, Any]:
    """Build stdin ingest payloads."""

    detection, hits = ingest_hits(facts, project_root, stdin)
    hits = hits[:MAX_LEXICAL_HITS]
    next_actions = hit_next_actions(hits)
    notes = _ingest_notes(detection, hits)
    if not hits and _empty_stdin(detection):
        next_actions = _empty_stdin_actions()
    return {
        "header": header(
            "ingest",
            {
                "source": detection["source"],
                "hit": len(hits),
                "bytes": detection["byteCount"],
            },
        ),
        "inputDetection": detection,
        "owners": owners_for_paths(
            facts, project_root, [hit["ownerPath"] for hit in hits]
        ),
        "hits": hits,
        "nextActions": next_actions,
        "notes": notes,
    }


def _ingest_notes(
    detection: dict[str, Any], hits: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if hits:
        return []
    if _empty_stdin(detection):
        return [
            {
                "kind": "stdin-required",
                "message": (
                    "search ingest consumes stdin candidate paths; "
                    "use search prime --view seeds for project discovery"
                ),
            }
        ]
    return [{"kind": "unrecognized-input", "message": "stdin produced no path hits"}]


def _empty_stdin(detection: dict[str, Any]) -> bool:
    return detection["byteCount"] == 0 and detection["lineCount"] == 0


def _empty_stdin_actions() -> list[dict[str, str]]:
    return [
        {
            "kind": "prime",
            "target": "search prime --view seeds",
            "scope": "project-discovery",
        },
        {
            "kind": "ingest",
            "target": "pipe candidate paths into search ingest items tests --view seeds",
            "scope": "stdin-candidates",
        },
    ]
