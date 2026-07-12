"""Semantic-language registry metadata for the Python provider."""

from __future__ import annotations

from typing import Any

from . import _semantic_language_ids as ids
from ._semantic_language_benchmark import python_search_benchmark_invocation
from ._semantic_language_catalog import python_search_view_descriptors
from ._semantic_language_query import python_query_method_descriptors
from ._semantic_language_schemas import python_semantic_language_schemas

_PYTHON_CHECK_METHODS = ("check/changed", "check/full")
_PYTHON_QUERY_METHODS = ("query", "query/owner-items", "query/owner-local-projection")
_PYTHON_AST_PATCH_METHODS = ("ast-patch/dry-run",)
_PYTHON_EVIDENCE_METHODS = ("evidence/graph", "evidence/analyze")
_PYTHON_AGENT_METHODS = ("agent/doctor", "agent/guide")
_PYTHON_SEARCH_VIEW_DESCRIPTORS = python_search_view_descriptors()
_PYTHON_SEARCH_VIEWS = tuple(
    descriptor["view"] for descriptor in _PYTHON_SEARCH_VIEW_DESCRIPTORS
)
_PYTHON_SEARCH_METHODS = tuple(f"search/{view}" for view in _PYTHON_SEARCH_VIEWS)


def semantic_language_registry_document(
    project_root: str | None = None,
) -> dict[str, Any]:
    """Return the provider registry document advertised by agent doctor."""

    payload: dict[str, Any] = {
        "registryId": ids.SEMANTIC_LANGUAGE_REGISTRY_ID,
        "registryVersion": ids.SEMANTIC_LANGUAGE_REGISTRY_VERSION,
        "protocolId": ids.SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": ids.SEMANTIC_LANGUAGE_PROTOCOL_VERSION,
        "languages": [python_semantic_language_registration()],
    }
    if project_root is not None:
        payload["projectRoot"] = project_root
    return payload


def python_semantic_language_registration() -> dict[str, Any]:
    """Return the Python semantic-language provider registration."""

    return {
        "languageId": ids.PYTHON_LANGUAGE_ID,
        "providerId": ids.PYTHON_PROVIDER_ID,
        "binary": ids.PYTHON_BINARY,
        "namespace": ids.PYTHON_PROVIDER_NAMESPACE,
        "displayName": "Python",
        "methods": [
            *_PYTHON_SEARCH_METHODS,
            *_PYTHON_QUERY_METHODS,
            *_PYTHON_CHECK_METHODS,
            *_PYTHON_AST_PATCH_METHODS,
            *_PYTHON_EVIDENCE_METHODS,
            *_PYTHON_AGENT_METHODS,
        ],
        "methodDescriptors": python_semantic_language_method_descriptors(),
        "schemas": python_semantic_language_schemas(),
    }


def python_semantic_language_method_descriptors() -> list[dict[str, Any]]:
    """Return method descriptors for the Python provider registry."""

    descriptors = [
        _python_search_method_descriptor(descriptor)
        for descriptor in _PYTHON_SEARCH_VIEW_DESCRIPTORS
    ]
    descriptors.extend(python_query_method_descriptors())
    descriptors.extend(
        {
            "method": method,
            "command": "check",
            "supportsJson": True,
            "supportsCompact": True,
        }
        for method in _PYTHON_CHECK_METHODS
    )
    descriptors.extend(
        {
            "method": method,
            "command": "ast-patch",
            "input": "semantic-ast-patch packet",
            "requiredOptions": ["--packet"],
            "outputSchemaIds": ["agent.semantic-protocols.semantic-ast-patch-receipt"],
            "supportsJson": True,
            "supportsCompact": False,
            "mutationAvailable": False,
        }
        for method in _PYTHON_AST_PATCH_METHODS
    )
    descriptors.extend(
        [
            {
                "method": "evidence/graph",
                "command": "evidence",
                "input": "provider project root",
                "outputSchemaIds": [ids.SEMANTIC_EVIDENCE_GRAPH_SCHEMA_ID],
                "supportsJson": True,
                "supportsCompact": True,
            },
            {
                "method": "evidence/analyze",
                "command": "evidence",
                "input": "provider project root",
                "outputSchemaIds": [ids.SEMANTIC_GRAPH_TURBO_REQUEST_SCHEMA_ID],
                "packetSchemas": ["semantic-graph-turbo-request.v1"],
                "clients": ["asp-graph-turbo"],
                "supportsJson": True,
                "supportsCompact": True,
            },
        ]
    )
    descriptors.extend(
        [
            {
                "method": "agent/doctor",
                "command": "agent",
                "outputSchemaIds": [ids.SEMANTIC_LANGUAGE_REGISTRY_ID],
                "supportsJson": True,
                "supportsCompact": True,
            },
            {
                "method": "agent/guide",
                "command": "agent",
                "supportsJson": False,
                "supportsCompact": True,
            },
        ]
    )
    return descriptors


def _python_search_method_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    rendered = {
        **descriptor,
        "benchmarkInvocation": python_search_benchmark_invocation(
            str(descriptor["view"])
        ),
        "outputSchemaIds": _search_output_schema_ids(descriptor["view"]),
        "supportsJson": True,
        "supportsCompact": True,
    }
    if descriptor["view"] == "semantic-facts":
        rendered["supportsCompact"] = False
        rendered["outputModes"] = ["json"]
        rendered["packetSchemas"] = [
            "semantic-fact-graph.v1",
            "semantic-fact-ontology.v1",
        ]
        rendered["input"] = "search semantic-facts <query>"
    return rendered


def _search_output_schema_ids(view: str) -> list[str]:
    if view == "semantic-facts":
        return [ids.SEMANTIC_FACT_GRAPH_SCHEMA_ID]
    schema_ids = [ids.SEMANTIC_SEARCH_PACKET_SCHEMA_ID]
    if view == "public-external-types":
        schema_ids.append(ids.SEMANTIC_TYPE_SURFACE_SCHEMA_ID)
    if view == "policy":
        schema_ids.append("agent.semantic-protocols.semantic-handle")
    return schema_ids


def python_semantic_search_view_descriptor(view: str) -> dict[str, Any] | None:
    """Return the registry descriptor for one search view."""

    return next(
        (
            descriptor
            for descriptor in _PYTHON_SEARCH_VIEW_DESCRIPTORS
            if descriptor["view"] == view
        ),
        None,
    )


def is_python_semantic_search_view(view: str) -> bool:
    """Return whether a view is implemented by the Python provider."""

    return python_semantic_search_view_descriptor(view) is not None
