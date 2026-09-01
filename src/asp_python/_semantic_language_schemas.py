"""Provider-owned schema registrations for the Python semantic language."""

from __future__ import annotations

from . import _semantic_language_ids as ids


def python_semantic_language_schemas() -> list[dict[str, str]]:
    """Return only schemas owned by the Python provider."""

    return [
        {
            "schemaId": ids.PYTHON_CAPABILITIES_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/python-semantic-capabilities.v1.schema.json",
        }
    ]
