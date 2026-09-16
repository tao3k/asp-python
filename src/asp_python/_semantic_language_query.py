"""Query method descriptors for the Python semantic-language registry."""

from __future__ import annotations

from typing import Any

from . import _semantic_language_ids as ids
from ._tree_sitter_query_catalog import (
    PYTHON_TREE_SITTER_GRAMMAR_ID,
    PYTHON_TREE_SITTER_GRAMMAR_PROFILE_PATH,
    PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION,
    python_tree_sitter_query_catalog_descriptors,
)


def python_query_method_descriptors() -> list[dict[str, Any]]:
    """Return parser-owned query descriptors for the Python provider registry."""

    return [
        {
            "method": "query",
            "command": "query",
            "input": "catalog-id",
            "requiredOptions": ["--catalog|--treesitter-query"],
            "outputSchemaIds": [ids.SEMANTIC_TREE_SITTER_QUERY_SCHEMA_ID],
            "packetSchemas": ["semantic-tree-sitter-query.v1"],
            "supportsJson": True,
            "supportsCompact": True,
            "outputModes": ["frontier", "json"],
            "queryInputForms": ["catalog-id", "s-expression"],
            "grammarId": PYTHON_TREE_SITTER_GRAMMAR_ID,
            "grammarProfileVersion": PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION,
            "grammarProfileSchema": "semantic-tree-sitter-grammar-profile.v1",
            "grammarProfilePath": PYTHON_TREE_SITTER_GRAMMAR_PROFILE_PATH,
            "adapterModes": ["native-projection"],
            "sourceAuthorities": ["native-parser-adapter", "native-parser"],
            "executionBackends": ["native-parser"],
            "renderProfiles": ["corpus-locator"],
            "queryCatalogs": python_tree_sitter_query_catalog_descriptors(),
            "supportedPredicates": [
                "#eq?",
                "#any-eq?",
                "#any-of?",
                "#match?",
                "#any-match?",
                "#not-eq?",
                "#not-match?",
            ],
            "unsupportedPredicates": [],
            "cacheReplay": False,
            "unsupportedPatternBehavior": "diagnostic",
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
