"""Build the Python provider's canonical semantic doctor-v1 response."""

import json
from hashlib import sha256
from typing import Any

from . import _semantic_language_ids as ids


def _provider_identity() -> dict[str, str]:
    """Return the provider identity owned by the executable contract.

    Installation and Runtime routing consume ``provider/asp-provider-registration.json``;
    the provider process uses the same compile-time identity constants and does not
    carry a second package-local provider manifest.
    """

    return {
        "languageId": ids.PYTHON_LANGUAGE_ID,
        "providerId": ids.PYTHON_PROVIDER_ID,
        "binary": ids.PYTHON_BINARY,
        "execution": "provider",
    }


def _jcs_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def semantic_provider_doctor_document() -> dict[str, Any]:
    """Return the Python provider canonical doctor-v1 response envelope."""
    from ._semantic_language import semantic_language_registry_document

    identity = _provider_identity()
    registry = semantic_language_registry_document()
    return {
        "schemaId": "agent.semantic-protocols.semantic-provider-doctor",
        "schemaVersion": "1",
        "schemaAuthority": "https://tao3k.github.io/agent-semantic-protocols/schemas/",
        "protocolId": ids.SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": ids.SEMANTIC_LANGUAGE_PROTOCOL_VERSION,
        **identity,
        "registrySchemaId": ids.SEMANTIC_LANGUAGE_REGISTRY_ID,
        "registrySchemaVersion": ids.SEMANTIC_LANGUAGE_REGISTRY_VERSION,
        "registry": registry,
        "registryDigest": f"sha256:{sha256(_jcs_bytes(registry)).hexdigest()}",
    }
