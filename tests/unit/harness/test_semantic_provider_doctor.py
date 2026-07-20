"""Validate the Python provider doctor-v2 response contract."""

import io
import json
from hashlib import sha256
from pathlib import Path

from python_lang_project_harness._cli import run_cli


def test_cli_agent_doctor_json_validates_v1_envelope_and_registry(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    envelope_keys = (
        "schemaId schemaVersion schemaAuthority protocolId protocolVersion languageId providerId binary "
        "execution registrySchemaId registrySchemaVersion registry registryDigest"
    )
    assert set(payload) == set(envelope_keys.split())
    assert payload["schemaId"] == "agent.semantic-protocols.semantic-provider-doctor"
    assert payload["schemaVersion"] == "1"
    assert payload["schemaAuthority"] == (
        "https://tao3k.github.io/agent-semantic-protocols/schemas/"
    )
    assert payload["protocolId"] == "agent.semantic-protocols.semantic-language"
    assert payload["protocolVersion"] == "1"
    assert payload["registrySchemaId"] == (
        "agent.semantic-protocols.semantic-language-registry"
    )
    assert payload["registrySchemaVersion"] == "1"

    registry = payload["registry"]
    registration = registry["languages"][0]
    assert registry["registryVersion"] == "1"
    assert (payload["languageId"], payload["providerId"], payload["binary"]) == (
        registration["languageId"],
        registration["providerId"],
        registration["binary"],
    )
    descriptors = registration["methodDescriptors"]
    assert len(descriptors) == len(registration["methods"]) == 34
    assert all(descriptor["invocation"]["argv"] for descriptor in descriptors)
    canonical = json.dumps(
        registry,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert payload["registryDigest"] == f"sha256:{sha256(canonical).hexdigest()}"
