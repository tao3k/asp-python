"""Shared next-action helpers for Python semantic-search views."""

from __future__ import annotations

from typing import Any


def hit_next_actions(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return bounded owner/tests follow-up actions for hits."""

    actions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for hit in hits:
        for action in (
            {"kind": "owner", "target": hit["ownerPath"]},
            {"kind": "tests", "target": hit["ownerPath"]},
        ):
            key = (action["kind"], action["target"])
            if key in seen:
                continue
            seen.add(key)
            actions.append(action)
            if len(actions) >= 8:
                return actions
    return actions
