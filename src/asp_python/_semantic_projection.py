"""Parser-owned projection metadata for Python semantic query packets."""

from collections.abc import Iterable
from typing import Any

_MAX_QUERY_PACKET_PROJECTION_NODES = 24


def semantic_query_projection(
    match: dict[str, Any],
    fields: dict[str, Any],
    code: str,
) -> dict[str, Any]:
    exact_read = str(match["read"])
    node_id = _projection_node_id(str(match["name"]))
    nodes = _semantic_outline_nodes(node_id, match, fields, code)
    node_count = len(nodes)
    nodes_truncated = node_count > _MAX_QUERY_PACKET_PROJECTION_NODES
    if nodes_truncated:
        nodes = nodes[:_MAX_QUERY_PACKET_PROJECTION_NODES]
    rendered_node_ids = _rendered_node_ids(nodes)
    return {
        "mode": "compact",
        "syntax": "save-token-ruff",
        "sourceAuthority": "native-parser",
        "sourceFingerprint": _source_fingerprint(exact_read, code),
        "compactSafety": {
            "literalPolicy": "summarize",
            "whitespacePolicy": "formatter-structural",
            "normalization": "none",
            "alignment": "parser-roundtrip",
            "exactReadRequired": True,
        },
        "losslessStructure": not nodes_truncated,
        "exactRead": exact_read,
        "nodeCount": node_count,
        "nodeLimit": _MAX_QUERY_PACKET_PROJECTION_NODES,
        "nodesTruncated": nodes_truncated,
        "nodes": nodes,
        "renderedNodeIds": rendered_node_ids,
        "renderedRows": _rendered_rows(nodes, rendered_node_ids),
        "omitted": _semantic_outline_omissions(
            match,
            exact_read,
            nodes_truncated=nodes_truncated,
            root_id=node_id,
        ),
        "expandActions": _semantic_expand_actions(
            node_id,
            exact_read,
            nodes,
        ),
    }


def _semantic_outline_nodes(
    root_id: str,
    match: dict[str, Any],
    fields: dict[str, Any],
    code: str,
) -> list[dict[str, Any]]:
    parser_nodes = fields.get("projectionNodes")
    if isinstance(parser_nodes, list) and parser_nodes:
        return _semantic_outline_parser_nodes(root_id, parser_nodes)
    exact_read = str(match["read"])
    nodes: list[dict[str, Any]] = []
    parent_stack: dict[int, str] = {0: root_id}
    for line in code.splitlines():
        label = line.strip()
        if not label:
            continue
        depth = max(0, _leading_spaces(line) // 2)
        node_index = len(nodes)
        kind = _outline_node_kind(label, node_index)
        role = _outline_node_role(label, node_index)
        node_id = (
            root_id
            if node_index == 0
            else _projection_child_id(root_id, kind, exact_read, label)
        )
        node: dict[str, Any] = {
            "id": node_id,
            "nativeId": _projection_native_id(kind, exact_read, label),
            "structuralFingerprint": _projection_structural_fingerprint(
                kind,
                role,
                exact_read,
                label,
            ),
            "kind": kind,
            "role": role,
            "label": label,
            "depth": depth,
            "read": exact_read,
        }
        if node_index > 0:
            node["parentId"] = _projection_parent_id(parent_stack, depth, root_id)
        flags = _outline_node_flags(label)
        if flags:
            node["flags"] = flags
        nodes.append(node)
        _projection_record_parent(parent_stack, depth, str(node["id"]))
    return nodes


def _semantic_outline_parser_nodes(
    root_id: str,
    parser_nodes: list[Any],
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    parent_stack: dict[int, str] = {0: root_id}
    for parser_node in parser_nodes:
        if not isinstance(parser_node, dict):
            continue
        node = _semantic_parser_node(root_id, parser_node, parent_stack, len(nodes))
        nodes.append(node)
        _projection_record_parent(parent_stack, int(node["depth"]), str(node["id"]))
    return nodes


def _semantic_parser_node(
    root_id: str,
    parser_node: dict[str, Any],
    parent_stack: dict[int, str],
    node_index: int,
) -> dict[str, Any]:
    depth = int(parser_node.get("depth", 0))
    kind = str(parser_node.get("kind", "statement"))
    role = str(parser_node.get("role", "unknown"))
    label = str(parser_node.get("label", "statement"))
    read = str(parser_node.get("read"))
    node_id = (
        root_id if node_index == 0 else _projection_child_id(root_id, kind, read, label)
    )
    node = {
        "id": node_id,
        "nativeId": _projection_native_id(kind, read, label),
        "structuralFingerprint": _projection_structural_fingerprint(
            kind,
            role,
            read,
            label,
        ),
        "kind": kind,
        "role": role,
        "label": label,
        "depth": depth,
        "read": read,
    }
    if node_index > 0:
        node["parentId"] = _projection_parent_id(parent_stack, depth, root_id)
    flags = parser_node.get("flags")
    if isinstance(flags, list) and flags:
        node["flags"] = [str(flag) for flag in flags]
    return node


def _projection_parent_id(
    parent_stack: dict[int, str],
    depth: int,
    root_id: str,
) -> str:
    parent_depths = [stack_depth for stack_depth in parent_stack if stack_depth < depth]
    if not parent_depths:
        return root_id
    return parent_stack[max(parent_depths)]


def _projection_record_parent(
    parent_stack: dict[int, str],
    depth: int,
    node_id: str,
) -> None:
    for stored_depth in list(parent_stack):
        if stored_depth >= depth:
            del parent_stack[stored_depth]
    parent_stack[depth] = node_id


def _rendered_node_ids(nodes: list[dict[str, Any]]) -> list[str]:
    return list(dict.fromkeys(str(node["id"]) for node in nodes if node.get("id")))


def _rendered_rows(
    nodes: list[dict[str, Any]],
    rendered_node_ids: list[str],
) -> list[dict[str, Any]]:
    by_id = {str(node["id"]): node for node in nodes if node.get("id")}
    rows: list[dict[str, Any]] = []
    for node_id in rendered_node_ids:
        node = by_id.get(node_id)
        if node is None:
            continue
        rows.append(
            {
                "nodeId": node_id,
                "rowKind": _rendered_row_kind(str(node.get("role", "unknown"))),
                "text": _rendered_row_text(node),
                "semanticWeight": _rendered_row_weight(node),
            }
        )
    return rows


def _rendered_row_text(node: dict[str, Any]) -> str:
    label = str(node.get("label", "")).strip()
    depth = int(node.get("depth", 0))
    return f"{'  ' * max(0, depth)}{label}".rstrip()


def _rendered_row_kind(role: str) -> str:
    if role in {
        "declaration",
        "mutation",
        "call",
        "control-flow",
        "terminal",
        "effect",
        "field",
        "delimiter",
    }:
        return role
    return "unknown"


def _rendered_row_weight(node: dict[str, Any]) -> int:
    role = str(node.get("role", "unknown"))
    if role in {"terminal", "control-flow", "mutation", "call", "effect"}:
        return 2
    return 1


def _projection_child_id(
    root_id: str,
    kind: str,
    read: str,
    label: str,
) -> str:
    return ":".join(
        [
            root_id,
            _safe_projection_id_part(kind),
            _safe_projection_id_part(read),
            _stable_projection_hash(label),
        ]
    )


def _projection_native_id(kind: str, read: str, label: str) -> str:
    return ":".join(
        [
            "python",
            _safe_projection_id_part(kind),
            _safe_projection_id_part(read),
            _stable_projection_hash(label),
        ]
    )


def _projection_structural_fingerprint(
    kind: str,
    role: str,
    read: str,
    label: str,
) -> str:
    return ":".join(
        [
            _safe_projection_id_part(kind),
            _safe_projection_id_part(role),
            _safe_projection_id_part(read),
            _stable_projection_hash(label),
        ]
    )


def _safe_projection_id_part(value: str) -> str:
    normalized = "".join(
        char if char.isalnum() or char in "_.-" else "-" for char in value
    ).strip("-")
    return normalized or "node"


def _stable_projection_hash(value: str) -> str:
    hash_value = 2_166_136_261
    for byte in value.encode("utf-8"):
        hash_value ^= byte
        hash_value = (hash_value * 16_777_619) % (2**32)
    return f"{hash_value:x}"


def _semantic_outline_omissions(
    match: dict[str, Any],
    exact_read: str,
    *,
    nodes_truncated: bool,
    root_id: str,
) -> list[dict[str, Any]]:
    omissions: list[dict[str, Any]] = []
    if bool(match.get("truncated")) or nodes_truncated:
        omissions.append(
            {
                "kind": "statement-tail",
                "reason": "compact projection capped a large item; expand exact read before editing",
                "nodeId": root_id,
                "read": exact_read,
            }
        )
    return omissions


def _semantic_expand_actions(
    root_id: str,
    exact_read: str,
    nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions = [
        {
            "kind": "exact-read",
            "target": root_id,
            "read": exact_read,
            "reason": "read exact source before editing",
        },
    ]
    seen_reads = {exact_read}
    for node in _hot_projection_nodes(nodes):
        read = str(node.get("read", ""))
        if not read or read in seen_reads:
            continue
        seen_reads.add(read)
        actions.append(
            {
                "kind": "exact-read",
                "target": str(node.get("id", root_id)),
                "read": read,
                "reason": f"expand {node.get('kind', 'statement')} node before editing",
            }
        )
        if len(actions) >= 8:
            break
    return actions


def _hot_projection_nodes(
    nodes: list[dict[str, Any]],
) -> Iterable[dict[str, Any]]:
    return (node for node in nodes if _is_hot_projection_node(node))


def _is_hot_projection_node(node: dict[str, Any]) -> bool:
    return str(node.get("role", "")) in {
        "control-flow",
        "terminal",
        "call",
        "mutation",
        "effect",
    }


def _outline_node_kind(label: str, index: int) -> str:
    if index == 0:
        return "declaration"
    if label.startswith("@"):
        return "decorator"
    if label.startswith("class "):
        return "class"
    if label.startswith("async def "):
        return "async_function"
    if label.startswith("def "):
        return "function"
    head = label.split(" ", 1)[0].rstrip(":")
    return head or "statement"


def _outline_node_role(label: str, index: int) -> str:
    if index == 0:
        return "declaration"
    if label.startswith(
        ("if ", "for ", "while ", "with ", "try:", "except ", "match ", "case ")
    ):
        return "control-flow"
    if label.startswith(("@", "class ", "def ", "async def ")):
        return "declaration"
    if label.startswith("call "):
        return "call"
    if label.startswith(("return", "raise", "break", "continue")):
        return "terminal"
    if label.startswith("await "):
        return "effect"
    if label.startswith("assign "):
        return "mutation"
    return "unknown"


def _outline_node_flags(label: str) -> list[str]:
    flags: list[str] = []
    if label.startswith(("if ", "match ", "case ")):
        flags.append("branch")
    if label.startswith("@"):
        flags.append("decorator")
    if label.startswith(("for ", "while ")):
        flags.append("loop")
    if label.startswith("call "):
        flags.append("call")
    if label.startswith("return"):
        flags.append("return")
    if label.startswith("raise"):
        flags.append("raise")
    if label.startswith("break"):
        flags.append("break")
    if label.startswith("continue"):
        flags.append("continue")
    if "await " in label:
        flags.append("await")
    if label.startswith("assign "):
        flags.append("mutation")
    return flags


def _source_fingerprint(exact_read: str, code: str) -> str:
    return f"{exact_read}:{len(code)}:{_stable_hash(code)}"


def _stable_hash(value: str) -> str:
    current = 5381
    for char in value:
        current = ((current * 33) ^ ord(char)) & 0xFFFFFFFF
    return f"{current:x}"


def _projection_node_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in "_.:-" else "_" for char in value)


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))
