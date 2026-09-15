"""Semantic-language registry metadata for the Python provider."""

from __future__ import annotations

from typing import Any

from . import _semantic_language_ids as ids
from ._semantic_language_invocation import attach_semantic_language_invocations
from ._semantic_language_query import python_query_method_descriptors
from ._semantic_language_schemas import python_semantic_language_schemas
from ._semantic_provider_doctor import _provider_identity
from ._semantic_query_pack import python_query_pack_descriptor

_PYTHON_QUERY_METHODS = (
    "query",
    "query/exact-selector-native-v1",
)
_PYTHON_AST_PATCH_METHODS = ("ast-patch/dry-run",)
_PYTHON_AGENT_METHODS = ("agent/doctor", "agent/guide")


def semantic_language_registry_document() -> dict[str, Any]:
    """Return the provider registry document advertised by agent doctor."""

    payload: dict[str, Any] = {
        "registryId": ids.SEMANTIC_LANGUAGE_REGISTRY_ID,
        "registryVersion": ids.SEMANTIC_LANGUAGE_REGISTRY_VERSION,
        "protocolId": ids.SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": ids.SEMANTIC_LANGUAGE_PROTOCOL_VERSION,
        "languages": [python_semantic_language_registration()],
    }
    return payload


def python_semantic_language_registration() -> dict[str, Any]:
    """Return the Python semantic-language provider registration."""

    identity = _provider_identity()
    return {
        "languageId": identity["languageId"],
        "providerId": identity["providerId"],
        "binary": identity["binary"],
        "namespace": ids.PYTHON_PROVIDER_NAMESPACE,
        "displayName": "Python",
        "methods": [
            *_PYTHON_QUERY_METHODS,
            *_PYTHON_AST_PATCH_METHODS,
            *_PYTHON_AGENT_METHODS,
        ],
        "methodDescriptors": python_semantic_language_method_descriptors(),
        "schemas": python_semantic_language_schemas(),
        "queryPackDescriptor": python_query_pack_descriptor(),
    }


def python_semantic_language_method_descriptors() -> list[dict[str, Any]]:
    """Return method descriptors for the Python provider registry."""

    descriptors: list[dict[str, Any]] = []
    descriptors.extend(python_query_method_descriptors())
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
                "method": "agent/doctor",
                "command": "agent",
                "outputSchemaIds": [
                    "agent.semantic-protocols.semantic-provider-doctor"
                ],
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
    return attach_semantic_language_invocations(descriptors)
