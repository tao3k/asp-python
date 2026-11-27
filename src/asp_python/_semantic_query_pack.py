"""Publish Python query-composition recipes for the shared registry."""

from typing import Any


def python_query_pack_descriptor() -> dict[str, Any]:
    """Return the authoritative Python query-pack descriptor."""
    return {
        "descriptorId": "python.query-pack",
        "descriptorVersion": "1",
        "languageId": "python",
        "semanticFactsDescriptorId": "python.semantic-facts",
        "termRoleOverrides": [],
        "recipes": [
            {
                "recipeId": "python-asyncio-runtime",
                "trigger": {
                    "match": "any",
                    "terms": ["asyncio", "task", "scheduling"],
                },
                "clauses": [
                    {
                        "intentAxes": ["concurrency"],
                        "roles": ["concept"],
                        "terms": ["asyncio", "task", "scheduling"],
                    }
                ],
            },
            {
                "recipeId": "python-context-lifecycle",
                "trigger": {
                    "match": "any",
                    "terms": ["contextmanager", "resource", "lifecycle"],
                },
                "clauses": [
                    {
                        "intentAxes": ["resource-lifecycle"],
                        "roles": ["concept"],
                        "terms": ["contextmanager", "resource", "lifecycle"],
                    }
                ],
            },
            {
                "recipeId": "python-stream-backpressure",
                "trigger": {
                    "match": "any",
                    "terms": ["queue", "async-generator", "backpressure"],
                },
                "clauses": [
                    {
                        "intentAxes": ["collection", "stream"],
                        "roles": ["concept"],
                        "terms": ["queue", "async-generator", "backpressure"],
                    }
                ],
            },
        ],
    }
