"""Owner and import-edge facts for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import location, semantic_search_display_path
from ._semantic_search_model import Fields
from .verification.facts import is_test_path

if TYPE_CHECKING:
    from collections.abc import Iterable

    from python_lang_parser import (
        PythonReasoningTreeFacts,
        PythonReasoningTreeNode,
    )


def owner_nodes(facts: PythonReasoningTreeFacts) -> tuple[PythonReasoningTreeNode, ...]:
    """Return parser-valid reasoning-tree owner nodes."""

    return tuple(node for node in facts.nodes if node.is_valid)


def ranked_owner_records(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
) -> list[dict[str, Any]]:
    """Return owners ranked for a prime packet."""

    records = [owner_record(node, project_root) for node in owner_nodes(facts)]
    return sorted(
        records,
        key=lambda owner: (
            1 if owner["fields"].get("surface") == "test" else 0,
            0 if owner["public"] else 1,
            -int(owner["fields"].get("lines", 0)),
            owner["path"].count("/"),
            owner["path"],
        ),
    )


def owner_record(node: PythonReasoningTreeNode, project_root: Path) -> dict[str, Any]:
    """Return one semantic-search owner record."""

    path = semantic_search_display_path(node.path, project_root)
    exports = list(node.public_names)
    fields: Fields = {
        "kind": node.kind,
        "surface": "test" if is_test_path(path) else "source",
        "doc": node.has_intent_doc,
        "lines": node.effective_code_lines,
        "exportKind": node.export_contract_kind,
    }
    if node.child_names:
        fields["children"] = list(node.child_names[:8])
    return {
        "path": path,
        "namespace": ".".join(node.namespace),
        "role": _owner_role(node, path),
        "public": node.has_public_surface,
        "exports": exports,
        "nextActions": [
            {"kind": "owner", "target": path},
            {"kind": "tests", "target": path},
            *(
                {"kind": "text", "target": name, "ownerPath": path}
                for name in exports[:2]
            ),
        ],
        "fields": fields,
    }


def matching_owner_nodes(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> list[PythonReasoningTreeNode]:
    """Return owner nodes matching a path, namespace, or public export."""

    query_folded = query.casefold()
    matches = []
    for node in facts.nodes:
        path = semantic_search_display_path(node.path, project_root)
        namespace = ".".join(node.namespace)
        if (
            query_folded in path.casefold()
            or query_folded in namespace.casefold()
            or any(query_folded in name.casefold() for name in node.public_names)
        ):
            matches.append(node)
    return sorted(
        matches, key=lambda node: semantic_search_display_path(node.path, project_root)
    )


def owners_for_paths(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    paths: Iterable[str],
) -> list[dict[str, Any]]:
    """Return owner records for display paths."""

    wanted = set(paths)
    return [
        owner_record(node, project_root)
        for node in facts.nodes
        if semantic_search_display_path(node.path, project_root) in wanted
    ]


def import_edges(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Return parser-resolved import edges."""

    edges = []
    for edge in facts.import_edges[:limit]:
        importer = semantic_search_display_path(edge.importer_path, project_root)
        imported = semantic_search_display_path(edge.imported_path, project_root)
        edges.append(
            {
                "from": f"O:{importer}",
                "kind": "import",
                "to": f"O:{imported}",
                "location": location(importer, edge.line, edge.column),
                "fields": {
                    "import": edge.import_name,
                    "bound": edge.bound_name,
                    "scope": edge.scope or "module",
                    "relative": edge.is_relative,
                },
            }
        )
    return edges


def test_edges(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    owner_paths: set[str],
) -> list[dict[str, Any]]:
    """Return test-import edges for selected owners."""

    edges = []
    for edge in facts.import_edges:
        importer = semantic_search_display_path(edge.importer_path, project_root)
        imported = semantic_search_display_path(edge.imported_path, project_root)
        if not is_test_path(importer):
            continue
        if owner_paths and imported not in owner_paths:
            continue
        edges.append(
            {
                "from": f"O:{imported}",
                "kind": "test",
                "to": f"O:{importer}",
                "location": location(importer, edge.line, edge.column),
                "fields": {"import": edge.import_name, "scope": edge.scope or "module"},
            }
        )
    return edges


def _owner_role(node: PythonReasoningTreeNode, path: str) -> str:
    if is_test_path(path):
        return "test"
    if node.parent_namespace is None:
        return f"root,{node.kind}"
    if node.has_public_surface:
        return f"public,{node.kind}"
    return node.kind
