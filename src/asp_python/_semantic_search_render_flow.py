"""Flow, note, and synthesis renderers for semantic-search packets."""

from __future__ import annotations

from typing import Any

from ._semantic_search_common import escape_field_value, escape_scalar, render_fields
from ._semantic_search_render_lines import (
    render_next_action,
)


def finding_lines(packet: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for finding in packet["findings"]:
        location = finding["location"]
        fields: dict[str, Any] = {
            "path": location["path"],
        }
        if "line" in location:
            fields["line"] = location["line"]
        if "column" in location:
            fields["column"] = location["column"]
        fields["node"] = f"O:{location['path']}"
        fields["severity"] = finding["severity"]
        lines.append(
            f"|find {finding['ruleId']} x{finding['count']} {render_fields(fields)}".rstrip()
        )
    return lines


def note_lines(packet: dict[str, Any]) -> list[str]:
    return [
        f"|note kind={note['kind']} message={escape_field_value(note['message'])}"
        for note in packet["notes"]
    ]


def synthesis_lines(packet: dict[str, Any]) -> list[str]:
    synthesis = packet.get("searchSynthesis")
    if not synthesis:
        return []
    fields = {
        "algorithm": synthesis.get("algorithm", ""),
        "scope": synthesis.get("scope", ""),
        "summary": synthesis.get("summary", ""),
        "ownerPath": synthesis.get("ownerPath", ""),
        "selectedOwners": synthesis.get("selectedOwners", ""),
        "selectedEdges": synthesis.get("selectedEdges", ""),
        "incomingOwners": synthesis.get("incomingOwners", ""),
        "outgoingOwners": synthesis.get("outgoingOwners", ""),
        "highImpactOwners": synthesis.get("highImpactOwners", []),
        "frontierOwners": synthesis.get("frontierOwners", []),
        "editFrontier": synthesis.get("editFrontier", []),
        "testFrontier": synthesis.get("testFrontier", []),
        "windowSet": [
            render_next_action(action) for action in synthesis.get("windowSet", [])
        ],
        "findingOwners": synthesis.get("findingOwners", []),
    }
    lines = [f"|synthesis {render_fields(fields)}".rstrip()]
    seeds = synthesis.get("seeds", [])
    if seeds:
        lines.extend(_seed_action_lines(seeds))
    return lines


def avoid_next_action_lines(packet: dict[str, Any]) -> list[str]:
    return [
        f"|avoid {render_next_action(action)} reason={escape_scalar(action['reason'])}"
        for action in packet.get("avoidNextActions", [])
    ]


def seed_packet_text(packet: dict[str, Any]) -> str:
    from ._semantic_search_graph_render import compact_graph_seed_packet_text

    return compact_graph_seed_packet_text(packet, render_fields)


def _seed_lines(packet: dict[str, Any]) -> list[str]:
    groups = _seed_groups(packet)
    return [f"|seed {kind}:{','.join(values)}" for kind, values in groups.items()]


def _seed_action_lines(actions: list[dict[str, Any]]) -> list[str]:
    groups: dict[str, list[str]] = {}
    for action in actions:
        kind = action.get("kind")
        target = action.get("target")
        if isinstance(kind, str) and isinstance(target, str):
            _add_seed(groups, kind, target)
    return [f"|seed {kind}:{','.join(values)}" for kind, values in groups.items()]


def _seed_groups(packet: dict[str, Any]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for owner in packet["owners"]:
        _add_seed(groups, "owner", owner["path"])
        for export_name in owner.get("exports", [])[:4]:
            _add_seed(groups, "symbol", export_name)
    for hit in packet["hits"]:
        _add_seed(groups, "owner", hit["ownerPath"])
        if "symbol" in hit:
            _add_seed(groups, "symbol", hit["symbol"])
    for handle in packet.get("semanticHandles", []):
        owner_path = handle.get("implementationOwnerPath") or handle.get("ownerPath")
        if isinstance(owner_path, str):
            _add_seed(groups, "owner", owner_path)
        for test_path in handle.get("testPaths", [])[:4]:
            _add_seed(groups, "tests", test_path)
    for action in packet["nextActions"]:
        _add_seed(groups, action["kind"], action["target"])
    return groups


def _add_seed(groups: dict[str, list[str]], kind: str, target: str) -> None:
    values = groups.setdefault(kind, [])
    if len(values) >= 8 or target in values:
        return
    values.append(target)
