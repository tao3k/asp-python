"""Query method descriptors for the Python semantic-language registry."""

from __future__ import annotations

from typing import Any

from . import _semantic_language_ids as ids


def python_query_method_descriptors() -> list[dict[str, Any]]:
    """Return parser-owned query descriptors for the Python provider registry."""

    return [
        {
            "method": "query",
            "command": "query",
            "input": "catalog-id",
            "requiredOptions": ["--catalog"],
            "outputSchemaIds": [ids.AST_INSPECT_SCHEMA_ID],
            "packetSchemas": ["ast-inspect"],
            "supportsJson": True,
            "supportsCompact": True,
            "outputModes": ["frontier", "json"],
            "sourceAuthorities": ["native-parser"],
            "executionBackends": ["native-parser"],
        },
        {
            "method": "query/exact-selector-native-v1",
            "command": "query",
            "view": "exact-selector",
            "outputSchemaIds": [
                "agent.semantic-protocols.provider-native-exact-projection"
            ],
            "packetSchemas": [
                "provider-native-exact-request.v1",
                "provider-native-exact-response.v1",
            ],
            "requiresQuery": True,
            "acceptsStdin": True,
            "supportsPackageScope": False,
            "supportsJson": True,
            "supportsCompact": False,
        },
    ]
