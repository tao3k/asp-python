"""Graph-turbo request projection for Python evidence graphs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._evidence_graph import build_python_evidence_graph

_GRAPH_TURBO_REQUEST_SCHEMA_ID = "agent.semantic-protocols.semantic-graph-turbo-request"
_SEMANTIC_LANGUAGE_PROTOCOL_ID = "agent.semantic-protocols.semantic-language"


def build_python_evidence_analysis_request(project_root: Path) -> dict[str, Any]:
    """Return a graph-turbo request for the Python evidence graph."""

    graph = build_python_evidence_graph(project_root)
    analysis_graph = _analysis_graph(graph)
    summary = {
        "graphs": 1,
        "nodes": graph["summary"]["nodes"],
        "edges": graph["summary"]["edges"],
        "owners": graph["summary"]["owners"],
        "claims": graph["summary"]["claims"],
        "staleItems": graph["summary"]["staleItems"],
        "gaps": graph["summary"]["gaps"],
    }
    return {
        "schemaId": _GRAPH_TURBO_REQUEST_SCHEMA_ID,
        "schemaVersion": "1",
        "protocolId": _SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": "1",
        "packetKind": "graph-turbo-request",
        "requestId": (
            "python.evidence.analysis."
            f"graphs-{summary['graphs']}.nodes-{summary['nodes']}.gaps-{summary['gaps']}"
        ),
        "surface": "evidence-analyze",
        "queryTerms": ["python evidence quality"],
        "profile": "evidence-quality",
        "algorithm": "typed-ppr-diverse",
        "seedIds": _analysis_seed_ids(analysis_graph),
        "budget": 8,
        "producer": graph["producer"],
        "project": _analysis_project(project_root.resolve(), graph),
        "summary": summary,
        "graphs": [analysis_graph],
        "fields": {
            "next": "pipe JSON to `asp graph render --packet - --view seeds`",
        },
    }


def render_python_evidence_analysis_request(request: dict[str, Any]) -> str:
    """Render an agent-facing compact graph-turbo request summary."""

    summary = request["summary"]
    return (
        "evidence-analysis "
        f"profile={request['profile']} graphs={summary['graphs']} "
        f"nodes={summary['nodes']} edges={summary['edges']} "
        f"owners={summary['owners']} claims={summary['claims']} "
        f"stale-items={summary['staleItems']} gaps={summary['gaps']} "
        'next="asp graph render --packet - --view seeds"\n'
    )


def render_python_evidence_analysis_request_json(request: dict[str, Any]) -> str:
    """Render graph-turbo request JSON."""

    return json.dumps(request, separators=(",", ":")) + "\n"


def _analysis_graph(graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "graphId": graph["graphId"],
        "summary": graph["summary"],
        "nodes": [_analysis_node(node) for node in graph["nodes"]],
        "edges": [_analysis_edge(edge) for edge in graph["edges"]],
        "gaps": graph.get("gaps", []),
    }


def _analysis_node(node: dict[str, Any]) -> dict[str, Any]:
    location = node.get("location") if isinstance(node.get("location"), dict) else {}
    path = node.get("ownerPath") or location.get("path")
    line = location.get("line")
    rendered: dict[str, Any] = {
        "id": node["nodeId"],
        "kind": node["kind"],
        "role": _node_role(str(node["kind"])),
        "value": node["label"],
        "fields": dict(node.get("fields", {})),
    }
    if path is not None:
        rendered["path"] = path
        rendered["ownerPath"] = node.get("ownerPath", path)
    if isinstance(line, int):
        rendered["locator"] = f"{path}:{line}:{line}"
        rendered["startLine"] = line
        rendered["endLine"] = line
    for key in ("candidateId", "receiptId", "actionId", "summary", "status"):
        if key in node:
            rendered["fields"][key] = str(node[key])
    return rendered


def _analysis_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": edge["fromNodeId"],
        "target": edge["toNodeId"],
        "relation": edge["kind"],
        "fields": {"edgeId": edge["edgeId"]},
    }


def _analysis_seed_ids(graph: dict[str, Any]) -> list[str]:
    seeds = [str(node["id"]) for node in graph["nodes"] if node.get("kind") == "owner"]
    if seeds:
        return seeds
    nodes = graph["nodes"]
    return [str(nodes[0]["id"])] if nodes else []


def _analysis_project(root: Path, graph: dict[str, Any]) -> dict[str, Any]:
    project = graph.get("project", {})
    package = project.get("package") if isinstance(project, dict) else None
    return {"root": str(root), "package": package, "fields": {}}


def _node_role(kind: str) -> str:
    return {
        "owner": "path",
        "invariant-candidate": "claim",
        "verification-receipt": "receipt",
        "review-action": "action",
    }.get(kind, "evidence")
