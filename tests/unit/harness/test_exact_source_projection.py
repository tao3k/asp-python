from __future__ import annotations

import base64
import io
import json

from python_lang_project_harness._cli import run_cli


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
            "providerId": "py-harness",
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
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = run_cli(
            [
                "query",
                "--selector",
                selector,
                "--json",
                "--asp-provider-id",
                "py-harness",
                "--asp-parser-identity-digest",
                parser_digest,
                "--asp-query-pack-digest",
                query_pack_digest,
                "--asp-exact-request-stdin",
            ],
            stdin=json.dumps(request),
            stdout=stdout,
            stderr=stderr,
            cwd=tmp_path,
        )
        assert exit_code == 0, stderr.getvalue()
        return json.loads(stdout.getvalue())

    skeleton = invoke(root_selector, "callable-skeleton")
    payload = skeleton["projectionPayload"]
    assert isinstance(payload, dict)
    assert payload["schemaVersion"] == "1"
    nodes = payload["nodes"]
    assert isinstance(nodes, list)
    branch_selector = next(
        node["exactSelector"]["selector"] for node in nodes if node["kind"] == "branch"
    )

    branch = invoke(branch_selector, "source")
    assert branch["schemaVersion"] == "1"
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
        "providerId": "py-harness",
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
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = run_cli(
        [
            "query",
            "--selector",
            selector,
            "--asp-provider-id",
            "py-harness",
            "--asp-parser-identity-digest",
            "b" * 64,
            "--asp-query-pack-digest",
            "c" * 64,
            "--asp-exact-request-stdin",
        ],
        stdin=json.dumps(request),
        stdout=stdout,
        stderr=stderr,
        cwd=tmp_path,
    )

    assert exit_code == 0, stderr.getvalue()
    packet = json.loads(stdout.getvalue())
    assert packet["sourceContentDigest"] == "asp-owned-content-identity"
