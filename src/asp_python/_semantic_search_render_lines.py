"""Line renderers for Python semantic-search packet facts."""

from __future__ import annotations

from typing import Any

from ._semantic_search_common import escape_scalar, render_fields, render_location
from ._semantic_search_model import Fields
from .verification.facts import is_test_path

COMPACT_PIPE_OWNER_LINES = 4
COMPACT_PIPE_HIT_LINES = 6
COMPACT_PIPE_EDGE_LINES = 4


def package_lines(packet: dict[str, Any]) -> list[str]:
    return [
        f"|package {package['id']} {render_fields(package['fields'])}".rstrip()
        for package in packet.get("packages", [])
    ]


def node_lines(packet: dict[str, Any]) -> list[str]:
    allowed = {"owner", "dependency", "test", "symbol", "package"}
    return [
        f"|{node['kind']} {node.get('path') or node['id']} {render_fields(node['fields'])}".rstrip()
        for node in packet["nodes"]
        if node["kind"] in allowed
    ]


def owner_lines(packet: dict[str, Any]) -> list[str]:
    lines = []
    for owner in _compact_items(packet, packet["owners"], COMPACT_PIPE_OWNER_LINES):
        fields: Fields = {
            "role": owner["role"],
            "public": owner["public"],
            "exp": owner.get("exports", [])[:4],
            **owner["fields"],
        }
        owner_next = render_owner_next_actions(
            owner["path"],
            owner.get("nextActions", []),
        )
        if owner_next:
            fields["next"] = owner_next
        lines.append(f"|owner {owner['path']} {render_fields(fields)}".rstrip())
    return lines


def hit_lines(
    packet: dict[str, Any],
    owner_by_path: dict[str, dict[str, Any]],
) -> list[str]:
    lines = []
    for hit in _compact_hits(packet):
        owner_path = hit["ownerPath"]
        location = hit["location"]
        owner_role = owner_by_path.get(owner_path, {}).get("role")
        fields: Fields = {
            "kind": hit["kind"],
            "score": hit["score"],
            "reason": hit["reason"],
            **({"symbol": hit["symbol"]} if "symbol" in hit else {}),
            **({"owner": owner_path} if owner_path != location.get("path") else {}),
            **_hit_evidence_fields(packet, owner_role, hit),
            **hit.get("fields", {}),
        }
        line_kind = "api" if hit["kind"] == "api" else "hit"
        lines.append(
            f"|{line_kind} {render_location(location)} {render_fields(fields)}".rstrip()
        )
    return lines


def query_coverage_lines(packet: dict[str, Any]) -> list[str]:
    lines = []
    for query in packet.get("queryCoverage", []):
        fields: Fields = {
            "status": query["status"],
            "hit": query["hitCount"],
            "selected": query.get("fields", {}).get("selectedHits", 0),
            **({"surface": query["surfaces"][:4]} if query.get("surfaces") else {}),
            **({"owner": query["ownerPaths"][:4]} if query.get("ownerPaths") else {}),
        }
        lines.append(f"|query {escape_scalar(query['value'])} {render_fields(fields)}")
    return lines


def handle_lines(packet: dict[str, Any]) -> list[str]:
    lines = []
    for handle in packet.get("semanticHandles", []):
        raw_fields = {
            "kind": handle["kind"],
            "source": handle["source"],
            "title": handle["title"],
            "owner": handle.get("ownerPath"),
            "implementation": handle.get("implementationOwnerPath"),
            "tests": handle.get("testPaths", [])[:4],
            **handle.get("fields", {}),
        }
        fields = {
            key: value
            for key, value in raw_fields.items()
            if value is not None and value != [] and value != ""
        }
        lines.append(f"|handle {handle['id']} {render_fields(fields)}".rstrip())
    return lines


def edge_lines(packet: dict[str, Any]) -> list[str]:
    lines = []
    for edge in _compact_items(packet, packet["edges"], COMPACT_PIPE_EDGE_LINES):
        fields = (
            f" {render_fields(edge.get('fields', {}))}" if edge.get("fields") else ""
        )
        lines.append(f"|edge {edge['from']} -{edge['kind']}-> {edge['to']}{fields}")
    return lines


def render_owner_next_actions(
    owner_path: str,
    actions: list[dict[str, Any]],
) -> list[str]:
    return [
        render_next_action(action, context_owner_path=owner_path)
        for action in actions
        if action["kind"] != "owner" or action["target"] != owner_path
    ]


def render_next_action(
    action: dict[str, Any],
    *,
    context_owner_path: str | None = None,
) -> str:
    suffix = ""
    if action.get("ownerPath") and action["ownerPath"] != context_owner_path:
        suffix = f"(owner={action['ownerPath']})"
    elif action.get("scope"):
        suffix = f"(scope={action['scope']})"
    return f"{action['kind']}:{escape_scalar(action['target'])}{suffix}"


def _compact_hits(packet: dict[str, Any]) -> list[dict[str, Any]]:
    hits = packet["hits"]
    if packet["view"] != "text":
        return _compact_items(packet, hits, COMPACT_PIPE_HIT_LINES)
    return sorted(hits, key=_text_hit_compact_rank)[:COMPACT_PIPE_HIT_LINES]


def _text_hit_compact_rank(hit: dict[str, Any]) -> tuple[int, int]:
    fields = hit.get("fields", {})
    if fields.get("source") == "parser-visible-source":
        return (0, -int(hit.get("score", 0)))
    if hit.get("kind") == "symbol":
        return (1, -int(hit.get("score", 0)))
    if hit.get("kind") == "export":
        return (2, -int(hit.get("score", 0)))
    return (3, -int(hit.get("score", 0)))


def _compact_items(
    packet: dict[str, Any],
    items: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    if packet["view"] in {"text", "ingest"}:
        return items[:limit]
    return items


def _hit_evidence_fields(
    packet: dict[str, Any],
    owner_role: str | None,
    hit: dict[str, Any],
) -> Fields:
    if packet["view"] not in {"text", "ingest"}:
        return {}
    owner_path = hit["ownerPath"]
    fields: Fields = {"surface": "test" if is_test_path(owner_path) else "source"}
    if owner_role:
        fields["ownerRole"] = owner_role
    if hit.get("snippet"):
        fields["text"] = hit["snippet"]
    return fields
