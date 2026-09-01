from __future__ import annotations

import base64

from asp_python._exact_source_projection import (
    project_provider_native_exact_request,
)


def test_callable_skeleton_child_selector_round_trips_to_source(tmp_path) -> None:
    source = (
        b"def selected(value: int) -> int:\n"
        b"    if value > 1:\n"
        b"        return value\n"
        b"    return 0\n"
    )
    root_selector = "python://src/example.py#item/function/selected"
    parser_digest = "b" * 64
    query_pack_digest = "c" * 64

    def invoke(selector: str, projection_kind: str) -> dict[str, object]:
        request = {
            "schemaId": "agent.semantic-protocols.provider-native-exact-request",
            "schemaVersion": "1",
            "languageId": "python",
            "providerId": "asp-python",
            "structuralSelector": selector,
            "ownerPath": "src/example.py",
            "projectionKind": projection_kind,
            "generationIdentityDigest": "a" * 64,
            "parserIdentityDigest": parser_digest,
            "queryPackDigest": query_pack_digest,
            "sourceDigest": "d" * 64,
            "sourceByteLength": len(source),
            "sourceEncoding": "base64",
            "sourceBytesBase64": base64.b64encode(source).decode(),
            "transport": "stdin-json",
        }
        return project_provider_native_exact_request(request, cwd=tmp_path)

    skeleton = invoke(root_selector, "callable-skeleton")
    payload = skeleton["projectionPayload"]
    assert isinstance(payload, dict)
    assert "schemaId" not in payload
    assert "schemaVersion" not in payload
    assert "projectionKind" not in payload
    assert "providerId" not in payload
    nodes = payload["nodes"]
    assert isinstance(nodes, list)
    branch_selector = next(
        node["selector"] for node in nodes if node["kind"] == "branch"
    )

    branch = invoke(branch_selector, "source")
    assert branch["schemaVersion"] == "1"
    assert branch["ownerPath"] == "src/example.py"
    assert branch["normalizedParserFacts"] == {
        "itemKind": "function",
        "itemName": "selected",
        "scopes": [],
    }
    assert branch["requestedStructuralSelector"] == branch_selector
    assert branch["structuralSelector"] == branch_selector
    assert branch["projectionText"] == "if value > 1:\n        return value"


def test_provider_does_not_recompute_asp_source_digest(tmp_path) -> None:
    source = b"def selected() -> int:\n    return 1\n"
    selector = "python://src/example.py#item/function/selected"
    request = {
        "schemaId": "agent.semantic-protocols.provider-native-exact-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "structuralSelector": selector,
        "ownerPath": "src/example.py",
        "projectionKind": "source",
        "generationIdentityDigest": "a" * 64,
        "parserIdentityDigest": "b" * 64,
        "queryPackDigest": "c" * 64,
        "sourceDigest": "asp-owned-content-identity",
        "sourceByteLength": len(source),
        "sourceEncoding": "base64",
        "sourceBytesBase64": base64.b64encode(source).decode(),
        "transport": "stdin-json",
    }
    packet = project_provider_native_exact_request(request, cwd=tmp_path)
    assert packet["sourceContentDigest"] == "asp-owned-content-identity"


def test_scoped_method_selector_resolves_the_declaring_type(tmp_path) -> None:
    source = (
        b"class Agent:\n"
        b"    def run(self) -> int:\n"
        b"        return 1\n\n"
        b"class Other:\n"
        b"    def run(self) -> int:\n"
        b"        return 2\n"
    )
    selector = (
        "python://src/example.py#item/method/run/scope/implementation-owner/type/Agent"
    )
    request = {
        "schemaId": "agent.semantic-protocols.provider-native-exact-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "structuralSelector": selector,
        "ownerPath": "src/example.py",
        "projectionKind": "source",
        "generationIdentityDigest": "a" * 64,
        "parserIdentityDigest": "b" * 64,
        "queryPackDigest": "c" * 64,
        "sourceDigest": "d" * 64,
        "sourceByteLength": len(source),
        "sourceEncoding": "base64",
        "sourceBytesBase64": base64.b64encode(source).decode(),
        "transport": "stdin-json",
    }

    packet = project_provider_native_exact_request(request, cwd=tmp_path)

    assert packet["projectionText"] == "def run(self) -> int:\n        return 1"
    assert packet["normalizedParserFacts"] == {
        "itemKind": "method",
        "itemName": "run",
        "scopes": [
            {
                "role": "implementation-owner",
                "ownerKind": "type",
                "ownerName": "Agent",
            }
        ],
    }
