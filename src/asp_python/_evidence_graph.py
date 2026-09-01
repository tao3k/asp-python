"""Provider-owned evidence graph packets for Python projects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_EVIDENCE_GRAPH_SCHEMA_ID = "agent.semantic-protocols.semantic-evidence-graph"
_EVIDENCE_GRAPH_PROTOCOL_ID = "agent.semantic-protocols.evidence-graph"
_LANGUAGE_ID = "python"
_PROVIDER_ID = "asp-python"
_NAMESPACE = "agent.semantic-protocols.languages.python.asp-python"


def build_python_evidence_graph(project_root: Path) -> dict[str, Any]:
    """Return a portable evidence graph for a Python project."""

    root = project_root.resolve()
    owner_path = _select_owner_path(root)
    owner_id = _node_id("python:owner", owner_path)
    claim_id = _node_id("python:claim", owner_path)
    receipt_id = _node_id("python:receipt", "policy-api")
    action_id = _node_id("python:action", "attach-policy-api-receipt")
    gap_id = _node_id("python:gap", f"{owner_path}:receipt")
    nodes: list[dict[str, Any]] = [
        {
            "nodeId": owner_id,
            "kind": "owner",
            "label": owner_path,
            "ownerPath": owner_path,
            "status": "current",
            "location": {"path": owner_path, "line": 1, "column": 0},
            "fields": {"languageId": _LANGUAGE_ID, "source": "provider-project"},
        },
        {
            "nodeId": claim_id,
            "kind": "invariant-candidate",
            "label": "Python provider behavior needs executable evidence",
            "ownerPath": owner_path,
            "candidateId": "python.evidence.project-harness",
            "status": "needs-injection",
            "summary": "Project-level Python policy and semantic search behavior should be linked to verification receipts.",
            "location": {"path": owner_path, "line": 1, "column": 0},
            "fields": {
                "sourceRuleId": "PY-EVIDENCE-GRAPH",
                "receiptKind": "policy-evaluation",
            },
        },
        {
            "nodeId": receipt_id,
            "kind": "verification-receipt",
            "label": "Python dependency policy API receipt",
            "receiptId": "python.policy.api",
            "status": "needs-injection",
            "summary": "Attach the receipt emitted by the Python dependency policy API before treating the claim as verified.",
            "fields": {
                "authority": "asp-python-api",
                "trigger": "pytest-plugin",
            },
        },
        {
            "nodeId": action_id,
            "kind": "review-action",
            "label": "Attach Python dependency policy API receipt",
            "actionId": "python.attach-policy-api-receipt",
            "status": "missing",
            "summary": "run-receipt",
            "fields": {
                "priority": "p0",
                "targetId": "python.evidence.project-harness",
            },
        },
    ]
    edges = [
        _edge("python:edge:owner-claim", "supports-claim", owner_id, claim_id),
        _edge("python:edge:claim-receipt", "requires-evidence", claim_id, receipt_id),
        _edge("python:edge:action-claim", "requires-evidence", action_id, claim_id),
    ]
    gaps = [
        {
            "gapId": gap_id,
            "ownerPath": owner_path,
            "summary": "No attached Python dependency policy API receipt for this evidence graph.",
            "severity": "warning",
            "fields": {"requiredReceiptId": "python.policy.api"},
        }
    ]
    return {
        "schemaId": _EVIDENCE_GRAPH_SCHEMA_ID,
        "schemaVersion": "1",
        "protocolId": _EVIDENCE_GRAPH_PROTOCOL_ID,
        "protocolVersion": "1",
        "graphId": "python.evidence.graph",
        "producer": _producer(),
        "project": _project(root),
        "summary": _summary(nodes, edges, gaps),
        "nodes": nodes,
        "edges": edges,
        "gaps": gaps,
        "fields": {
            "next": "pipe JSON to `asp graph render --packet - --view seeds`",
        },
    }


def render_python_evidence_graph(graph: dict[str, Any]) -> str:
    """Render an agent-facing compact evidence graph summary."""

    summary = graph["summary"]
    return (
        "evidence-graph "
        f"nodes={summary['nodes']} edges={summary['edges']} "
        f"owners={summary['owners']} claims={summary['claims']} "
        f"stale-items={summary['staleItems']} gaps={summary['gaps']}\n"
    )


def render_python_evidence_graph_json(graph: dict[str, Any]) -> str:
    """Render evidence graph JSON."""

    return json.dumps(graph, separators=(",", ":")) + "\n"


def _summary(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "owners": sum(1 for node in nodes if node["kind"] == "owner"),
        "claims": sum(1 for node in nodes if node["kind"] == "invariant-candidate"),
        "staleItems": sum(
            1 for node in nodes if node.get("status") in {"stale", "expired"}
        ),
        "gaps": len(gaps),
    }


def _producer() -> dict[str, str]:
    return {
        "languageId": _LANGUAGE_ID,
        "providerId": _PROVIDER_ID,
        "namespace": _NAMESPACE,
    }


def _project(root: Path) -> dict[str, Any]:
    project: dict[str, Any] = {"root": str(root), "fields": {}}
    package_name = _package_name(root)
    if package_name is not None:
        project["package"] = package_name
    return project


def _edge(
    edge_id: str,
    kind: str,
    from_node_id: str,
    to_node_id: str,
) -> dict[str, str]:
    return {
        "edgeId": edge_id,
        "kind": kind,
        "fromNodeId": from_node_id,
        "toNodeId": to_node_id,
    }


def _select_owner_path(root: Path) -> str:
    for candidate in ("pyproject.toml", "setup.cfg", "setup.py"):
        if (root / candidate).is_file():
            return candidate
    for source_root in ("src", "."):
        base = root / source_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            return _relative_path(root, path)
    return "."


def _package_name(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    from ._project_config import read_pyproject_payload

    value = read_pyproject_payload(pyproject)
    name = value.get("project", {}).get("name")
    return str(name) if name else None


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _node_id(prefix: str, raw: str) -> str:
    return f"{prefix}:{_sanitize_id_part(raw)}"


def _sanitize_id_part(raw: str) -> str:
    output = "".join(
        character.lower()
        if character.isascii()
        and (character.isalnum() or character in {".", "_", ":", "-"})
        else "."
        for character in raw
    )
    while ".." in output:
        output = output.replace("..", ".")
    return output.strip(".") or "root"
