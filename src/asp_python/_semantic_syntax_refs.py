"""Attach Python syntax-query provenance refs to semantic protocol packets."""

from __future__ import annotations

from typing import Any

PYTHON_OWNER_ITEMS_QUERY_REF = "semantic-tree-sitter-query/python-owner-items.v1"


def annotate_python_owner_item_syntax_refs(
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Attach parser-owned syntax refs to item fields and return packet refs."""

    match_refs: list[str] = []
    capture_refs: list[str] = []
    for item in items:
        fields = item.get("fields", {})
        if not isinstance(fields, dict):
            continue
        read = fields.get("read") or item.get("read")
        if not isinstance(read, str) or not read:
            continue

        match_ref = f"match.{len(match_refs) + 1}"
        capture_ref = f"capture.{len(capture_refs) + 1}"
        fields["syntaxQueryRef"] = PYTHON_OWNER_ITEMS_QUERY_REF
        fields["syntaxMatchRef"] = match_ref
        fields["syntaxCaptureRef"] = capture_ref
        match_refs.append(match_ref)
        capture_refs.append(capture_ref)

    if not match_refs:
        return None
    return {
        "syntaxQueryRef": PYTHON_OWNER_ITEMS_QUERY_REF,
        "syntaxMatchRefs": match_refs,
        "syntaxCaptureRefs": capture_refs,
    }


def attach_python_syntax_refs(
    packet: dict[str, Any],
    syntax_refs: dict[str, Any] | None,
) -> None:
    if syntax_refs is None:
        return
    packet["syntaxQueryRef"] = syntax_refs["syntaxQueryRef"]
    packet["syntaxMatchRefs"] = syntax_refs["syntaxMatchRefs"]
    packet["syntaxCaptureRefs"] = syntax_refs["syntaxCaptureRefs"]
