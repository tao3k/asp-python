"""Build the Python provider's canonical semantic doctor-v1 response."""

import json
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Any

from . import _semantic_language_ids as ids


def _provider_manifest() -> dict[str, Any]:
    packaged = files("python_lang_project_harness").joinpath(
        "asp-provider-manifest.json"
    )
    if packaged.is_file():
        return json.loads(packaged.read_text(encoding="utf-8"))
    checkout = (
        Path(__file__).resolve().parents[2] / "provider" / "asp-provider-manifest.json"
    )
    return json.loads(checkout.read_text(encoding="utf-8"))


def _provider_identity() -> dict[str, str]:
    manifest = _provider_manifest()
    keys = ("languageId", "providerId", "binary", "execution")
    identity = {key: manifest[key] for key in keys}
    if not all(isinstance(value, str) and value for value in identity.values()):
        raise ValueError("provider manifest identity fields must be non-empty strings")
    return identity


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
