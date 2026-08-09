"""Provider-owned graph facts for Python data-shape queries."""

from __future__ import annotations

import json
from pathlib import Path

from ._cli_args import ProtocolArgs
from ._semantic_graph_fact_collect import collect_field_facts
from ._semantic_graph_fact_render import graph_payload
from ._semantic_graph_project_collect import collect_project_facts
from ._semantic_graph_project_render import project_graph_payload


def render_semantic_graph_facts(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdin: str,
) -> str | None:
    """Render graph-turbo provider facts for Python field/type/collection queries."""

    if not _supports_semantic_graph_facts(args):
        return None
    field_payload = graph_payload(
        args.query or "",
        collect_field_facts(project_root, args.query or "", stdin),
    )
    project_payload = project_graph_payload(collect_project_facts(project_root))
    package_bridge_edges = _package_bridge_edges(field_payload, project_payload)
    payload = {
        "schemaId": "agent.semantic-protocols.semantic-fact-graph",
        "schemaVersion": "1",
        "protocolId": "agent.semantic-protocols.semantic-language",
        "protocolVersion": "1",
        "languageId": "python",
        "providerId": "py-harness",
        "projectRoot": project_root.as_posix(),
        "query": args.query or "",
        "nodes": [*field_payload["nodes"], *project_payload["nodes"]],
        "edges": [
            *field_payload["edges"],
            *project_payload["edges"],
            *package_bridge_edges,
        ],
    }
    return json.dumps(payload, sort_keys=True) + "\n"


def _supports_semantic_graph_facts(args: ProtocolArgs) -> bool:
    return (
        args.command == "search"
        and args.view == "semantic-facts"
        and args.json
        and args.query is not None
    )


def _package_bridge_edges(
    field_payload: dict[str, list[dict[str, object]]],
    project_payload: dict[str, list[dict[str, object]]],
) -> list[dict[str, str]]:
    package_id = next(
        (
            str(node["id"])
            for node in project_payload["nodes"]
            if node.get("kind") == "package" and isinstance(node.get("id"), str)
        ),
        None,
    )
    if package_id is None:
        return []
    return [
        {"source": str(node["id"]), "target": package_id, "relation": "belongs_to"}
        for node in field_payload["nodes"]
        if node.get("kind") in {"field", "hot", "owner"}
        and isinstance(node.get("id"), str)
    ]
