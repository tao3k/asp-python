"""Compact text rendering orchestration for Python search packets."""

from __future__ import annotations

from typing import Any

from ._semantic_search_common import compact_fields, render_fields
from ._semantic_search_render_flow import (
    avoid_next_action_lines,
    finding_lines,
    note_lines,
    seed_packet_text,
    synthesis_lines,
)
from ._semantic_search_render_lines import (
    edge_lines,
    hit_lines,
    node_lines,
    owner_lines,
    package_lines,
    query_coverage_lines,
    render_next_action,
)


def render_compact_packet(packet: dict[str, Any]) -> str:
    if packet["renderMode"] == "seeds":
        return seed_packet_text(packet)
    return "\n".join(_compact_packet_lines(packet)) + "\n"


def _compact_packet_lines(packet: dict[str, Any]) -> list[str]:
    if _is_item_inventory_packet(packet):
        return _item_inventory_packet_lines(packet)
    owner_by_path = {owner["path"]: owner for owner in packet["owners"]}
    lines = [
        f"[{packet['header']['kind']}] {render_fields(packet['header']['fields'])}"
    ]
    _extend_payload_lines(packet, owner_by_path, lines)
    _extend_flow_lines(packet, lines)
    return lines


def _is_item_inventory_packet(packet: dict[str, Any]) -> bool:
    fields = packet["header"]["fields"]
    return fields.get("itemQuery") is None and (
        bool(packet.get("items")) or fields.get("itemStatus") is not None
    )


def _item_inventory_packet_lines(packet: dict[str, Any]) -> list[str]:
    fields = packet["header"]["fields"]
    header_fields = compact_fields(
        {
            "profile": fields.get("profile"),
            "ownerPath": fields.get("ownerPath"),
            "query": fields.get("query"),
            "dependency": fields.get("dependency"),
            "returns": fields.get("returns"),
            "q": fields.get("q"),
            "owner": fields.get("owner"),
            "item": len(packet.get("items", [])),
            "pipes": fields.get("pipes"),
        }
    )
    lines = [f"[{packet['header']['kind']}] {render_fields(header_fields)}"]
    lines.extend(_item_inventory_owner_lines(packet))
    lines.extend(item_lines(packet))
    lines.extend(
        line for line in note_lines(packet) if "kind=item-not-found" not in line
    )
    lines.extend(runtime_cost_lines(packet))
    return lines


def _item_inventory_owner_lines(packet: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for owner in packet["owners"]:
        fields = {
            "role": owner["role"],
            "public": owner["public"],
            "exp": owner.get("exports", [])[:4],
            **owner["fields"],
        }
        lines.append(f"|owner {owner['path']} {render_fields(fields)}".rstrip())
    return lines


def _extend_payload_lines(
    packet: dict[str, Any],
    owner_by_path: dict[str, dict[str, Any]],
    lines: list[str],
) -> None:
    from ._semantic_search_render_lines import handle_lines

    lines.extend(item_query_lines(packet))
    lines.extend(query_coverage_lines(packet))
    lines.extend(package_lines(packet))
    lines.extend(node_lines(packet))
    lines.extend(owner_lines(packet))
    lines.extend(handle_lines(packet))
    lines.extend(item_lines(packet))
    lines.extend(code_lines(packet))
    lines.extend(hit_lines(packet, owner_by_path))
    if packet["view"] not in {"workspace", "prime"}:
        lines.extend(edge_lines(packet))
        lines.extend(finding_lines(packet))


def _extend_flow_lines(packet: dict[str, Any], lines: list[str]) -> None:
    lines.extend(note_lines(packet))
    lines.extend(runtime_cost_lines(packet))
    lines.extend(synthesis_lines(packet))
    lines.extend(avoid_next_action_lines(packet))
    lines.extend(
        f"|next {','.join(render_next_action(action) for action in packet['nextActions'])}"
        for _ in [None]
        if packet["nextActions"]
    )


def runtime_cost_lines(packet: dict[str, Any]) -> list[str]:
    runtime_cost = packet.get("runtimeCost")
    if not isinstance(runtime_cost, dict):
        return []
    fields = compact_fields(
        {
            "cache": runtime_cost.get("cacheStatus"),
            "elapsedMs": runtime_cost.get("elapsedMs"),
            "parseMs": runtime_cost.get("parseMs"),
            "sourceFiles": runtime_cost.get("sourceFilesParsed"),
            "packages": runtime_cost.get("packagesScanned"),
            "reused": runtime_cost.get("parserFactsReused"),
            **runtime_cost.get("fields", {}),
            "reason": runtime_cost.get("reason"),
        }
    )
    return [f"|runtime {render_fields(fields)}"]


def item_query_lines(packet: dict[str, Any]) -> list[str]:
    fields = packet["header"]["fields"]
    item_query = fields.get("itemQuery")
    if item_query is None:
        return []
    rendered = compact_fields(
        {
            "itemQuery": item_query,
            "status": fields.get("itemStatus"),
            "match": fields.get("itemMatch"),
            "item": fields.get("item"),
            "reason": "parser-item-query",
            "output": "names" if _item_query_names_only(fields) else None,
            "next": _item_query_next(fields),
        }
    )
    return [f"|query {render_fields(rendered)}"]


def item_lines(packet: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for item in packet.get("items", []):
        item_fields = item.get("fields", {})
        item_name = item["name"]
        fields = compact_fields(
            {
                "kind": item.get("kind"),
                "public": True if item_fields.get("public") is True else None,
                "doc": True if item_fields.get("doc") is True else None,
                "next": f"syntax:{item_name}",
                "structuralSelector": item_fields.get("structuralSelector"),
                "displayLineRange": item_fields.get("displayLineRange"),
                "sourceLocatorHint": item_fields.get("sourceLocatorHint"),
                "read": item_fields.get("read"),
                "syn": _syntax_atom_for_kind(item.get("kind")),
                "tsqRef": "semantic-tree-sitter-query/python-owner-items.v1",
            }
        )
        lines.append(f"|item {item['name']} {render_fields(fields)}")
    return lines


def _syntax_atom_for_kind(kind: object) -> str | None:
    if kind == "function":
        return "function_definition/name"
    if kind == "class":
        return "class_definition/name"
    if kind == "import":
        return "import_statement/name"
    if kind == "import-from":
        return "import_from_statement/name"
    return None


def code_lines(packet: dict[str, Any]) -> list[str]:
    if packet["header"]["fields"].get("itemQuery") is not None:
        return []
    lines: list[str] = []
    for item in packet.get("items", []):
        item_fields = item.get("fields", {})
        code = item_fields.get("code")
        if not isinstance(code, str) or not code:
            continue
        location = item.get("location", {})
        line_range = location.get("lineRange")
        if not isinstance(line_range, str) and location.get("line") is not None:
            line_range = f"{location['line']}:{location['line']}"
        fields = compact_fields(
            {
                "path": location.get("path"),
                "lineRange": line_range,
                "reason": item_fields.get("reason"),
                "truncated": item_fields.get("truncated"),
                "text": code,
            }
        )
        lines.append(f"|code {render_fields(fields)}")
    return lines


def _item_query_names_only(fields: dict[str, Any]) -> bool:
    if fields.get("itemQuery") is None:
        return False
    item = fields.get("item")
    item_count = item if isinstance(item, int) else 0
    if fields.get("itemStatus") == "miss":
        return True
    return item_count > 1 and fields.get("itemMatch") != "exact"


def _item_query_next(fields: dict[str, Any]) -> str:
    item = fields.get("item")
    item_count = item if isinstance(item, int) else 0
    if fields.get("itemStatus") == "miss" or item_count == 0:
        return "revise-query"
    if _item_query_names_only(fields) and item_count > 1:
        return "select-item"
    return "query-code"
