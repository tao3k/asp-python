"""Core workspace, prime, and owner semantic-search views."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import header, path_hit
from ._semantic_search_deps import dependency_node
from ._semantic_search_findings import finding_facts
from ._semantic_search_items import owner_item_query_payload
from ._semantic_search_model import (
    MAX_DEPENDENCY_HITS,
    MAX_IMPORT_HITS,
    MAX_PRIME_EDGES,
    MAX_PRIME_OWNERS,
    MAX_WORKSPACE_EDGES,
)
from ._semantic_search_owners import (
    import_edges,
    matching_owner_nodes,
    owner_nodes,
    owner_record,
    ranked_owner_records,
)
from ._semantic_search_packages import dependencies, project_name, workspace_packages

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport


def workspace_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
) -> dict[str, Any]:
    """Build the workspace/router packet payload."""

    packages = workspace_packages(report, facts, project_root, len(owner_nodes(facts)))
    edges = import_edges(facts, project_root, limit=MAX_WORKSPACE_EDGES)
    owners = _workspace_owner_records(packages)
    return {
        "header": header(
            "workspace",
            {
                "mode": "workspace-index",
                "package": project_name(facts),
                "packages": len(packages),
                "shown": len(packages),
                "edge": len(edges),
                "external": len(dependencies(facts)),
                "find": len(report.findings),
            },
        ),
        "packages": packages,
        "owners": owners,
        "edges": edges,
        "findings": finding_facts(report, project_root),
        "nextActions": [
            {"kind": "owner", "target": item["path"]} for item in owners[:8]
        ],
    }


def prime_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
) -> dict[str, Any]:
    """Build the prime project map payload."""

    owners = ranked_owner_records(facts, project_root)[:MAX_PRIME_OWNERS]
    dep_nodes = [dependency_node(item) for item in dependencies(facts)]
    edges = import_edges(facts, project_root, limit=MAX_PRIME_EDGES)
    findings = finding_facts(report, project_root)
    return {
        "header": header(
            "prime",
            {
                "mode": "prime-map",
                "package": project_name(facts),
                "owner": len(owner_nodes(facts)),
                "shown": len(owners),
                "edge": len(edges),
                "external": len(dep_nodes),
                "find": len(report.findings),
            },
        ),
        "nodes": dep_nodes[:MAX_DEPENDENCY_HITS],
        "owners": owners,
        "edges": edges,
        "findings": findings,
        "nextActions": _prime_next_actions(owners, dep_nodes),
        "searchSynthesis": _prime_graph_synthesis(
            owners,
            edges,
            findings,
        ),
    }


def owner_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
    *,
    pipes: tuple[str, ...] = (),
    item_query: str | None = None,
) -> dict[str, Any]:
    """Build an owner slice payload."""

    matches = matching_owner_nodes(facts, project_root, query)
    owners = [owner_record(node, project_root) for node in matches[:MAX_PRIME_OWNERS]]
    owner_paths = {owner["path"] for owner in owners}
    edges = [
        edge
        for edge in import_edges(facts, project_root, limit=MAX_IMPORT_HITS)
        if edge["from"].removeprefix("O:") in owner_paths
        or edge["to"].removeprefix("O:") in owner_paths
    ]
    findings = finding_facts(report, project_root, owner_paths=owner_paths)
    item_payload = (
        owner_item_query_payload(report, project_root, query, item_query)
        if "items" in pipes
        else {"items": [], "fields": {}, "notes": []}
    )
    return {
        "header": header(
            "owner",
            {
                "q": query,
                "owner": len(owners),
                "edge": len(edges),
                **item_payload["fields"],
            },
        ),
        "owners": owners,
        "edges": edges,
        "items": item_payload["items"],
        "hits": [
            path_hit(owner["path"], owner["path"], score=4, reason="owner-match")
            for owner in owners
        ],
        "findings": findings,
        "nextActions": _owner_next_actions(owners),
        "searchSynthesis": _owner_graph_synthesis(owners, edges, findings),
        "notes": [
            *([] if owners else [{"kind": "owner-not-found", "message": query}]),
            *item_payload["notes"],
        ],
    }


def _prime_next_actions(
    owners: list[dict[str, Any]],
    dep_nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for owner in owners[:3]:
        actions.append({"kind": "owner", "target": owner["path"]})
        if owner.get("exports"):
            actions.append(
                {
                    "kind": "text",
                    "target": owner["exports"][0],
                    "ownerPath": owner["path"],
                }
            )
    actions.extend(
        {"kind": "deps", "target": dependency}
        for dependency in _unique_dependencies(dep_nodes)
    )
    return actions[:8]


def _workspace_owner_records(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    owners: list[dict[str, Any]] = []
    for package in packages:
        package_id = str(package["id"])
        fields = dict(package.get("fields", {}))
        owners.append(
            {
                "path": package_id,
                "namespace": "." if package_id == "." else package_id.replace("/", "."),
                "role": fields.get("role", "workspace-package"),
                "public": True,
                "exports": [],
                "nextActions": [{"kind": "owner", "target": package_id}],
                "fields": {
                    "kind": "package",
                    "surface": fields.get("surface", "workspace"),
                    "name": fields.get("name", package_id),
                },
            }
        )
    return owners


def _owner_next_actions(owners: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for owner in owners[:8]:
        actions.append({"kind": "tests", "target": owner["path"]})
        actions.extend(
            {"kind": "text", "target": name, "ownerPath": owner["path"]}
            for name in owner.get("exports", [])[:2]
        )
    return actions


def _unique_dependencies(dep_nodes: list[dict[str, Any]]) -> list[str]:
    dependencies: list[str] = []
    seen: set[str] = set()
    for node in dep_nodes:
        dependency = node["id"].removeprefix("D:")
        if dependency in seen:
            continue
        seen.add(dependency)
        dependencies.append(dependency)
    return dependencies


def _prime_graph_synthesis(
    owners: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    selected_owners = [owner["path"] for owner in owners]
    if not selected_owners:
        return None
    frontier_owners = _frontier_owner_paths(selected_owners, edges)
    seeds = [{"kind": "owner", "target": path} for path in frontier_owners[:4]]
    return _compact_synthesis(
        {
            "algorithm": "owner-rank-frontier",
            "scope": "prime",
            "summary": "owner-graph-frontier",
            "selectedOwners": len(selected_owners),
            "selectedEdges": len(edges),
            "highImpactOwners": selected_owners[:4],
            "frontierOwners": frontier_owners[:4],
            "findingOwners": _finding_owner_paths(findings),
            "seeds": seeds,
        }
    )


def _owner_graph_synthesis(
    owners: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    selected_owners = [owner["path"] for owner in owners]
    if not selected_owners:
        return None
    incoming_owners, outgoing_owners = _incoming_outgoing_owner_paths(
        selected_owners,
        edges,
    )
    frontier_owners = _dedupe([*incoming_owners, *outgoing_owners])[:4]
    synthesis: dict[str, Any] = {
        "algorithm": "bounded-reachability-depth1",
        "scope": "owner",
        "summary": "owner-graph-frontier",
        "selectedOwners": len(selected_owners),
        "selectedEdges": len(edges),
        "incomingOwners": len(incoming_owners),
        "outgoingOwners": len(outgoing_owners),
        "frontierOwners": frontier_owners,
        "findingOwners": _finding_owner_paths(findings),
        "seeds": [{"kind": "owner", "target": path} for path in frontier_owners],
    }
    if len(selected_owners) == 1:
        synthesis["ownerPath"] = selected_owners[0]
    return _compact_synthesis(synthesis)


def _frontier_owner_paths(
    selected_owners: list[str],
    edges: list[dict[str, Any]],
) -> list[str]:
    incoming_owners, outgoing_owners = _incoming_outgoing_owner_paths(
        selected_owners,
        edges,
    )
    return _dedupe([*incoming_owners, *outgoing_owners])


def _incoming_outgoing_owner_paths(
    selected_owners: list[str],
    edges: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    selected = set(selected_owners)
    incoming: list[str] = []
    outgoing: list[str] = []
    for edge in edges:
        source = _owner_id_path(edge["from"])
        target = _owner_id_path(edge["to"])
        if source in selected and target not in selected:
            outgoing.append(target)
        if target in selected and source not in selected:
            incoming.append(source)
    return _dedupe(incoming), _dedupe(outgoing)


def _owner_id_path(owner_id: str) -> str:
    return owner_id.removeprefix("O:")


def _finding_owner_paths(findings: list[dict[str, Any]]) -> list[str]:
    return _dedupe(finding["location"]["path"] for finding in findings)[:4]


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _compact_synthesis(synthesis: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in synthesis.items()
        if value is not None and value != [] and value != ""
    }
