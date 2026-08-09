from __future__ import annotations

import base64
import json
from io import StringIO
from pathlib import Path

from blake3 import blake3

from python_lang_project_harness._cli import run_cli
from python_lang_project_harness._owner_search_stdin import (
    try_run_provider_native_owner,
)
from python_lang_project_harness._semantic_language import (
    python_semantic_language_method_descriptors,
)


def _request(source: bytes) -> dict[str, object]:
    return {
        "schemaId": "agent.semantic-protocols.provider-native-owner-search-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "py-harness",
        "workspaceIdentity": "workspace-test",
        "providerWorkspaceIdentityDigest": "1" * 64,
        "ownerPath": "src/example.py",
        "sourceFingerprint": {
            "fileIdentity": "resident-owner:test",
            "sizeBytes": len(source),
            "modifiedUnixNanos": 0,
            "changeTimeUnixNanos": 0,
            "contentDigest": blake3(source).hexdigest(),
        },
        "sourceEncoding": "base64",
        "sourceBytesBase64": base64.b64encode(source).decode("ascii"),
        "projectionMode": "complete-owner",
        "transport": "stdin-json",
    }


def test_owner_search_projects_complete_top_level_function_owner() -> None:
    source = (
        b"def alpha(value: int) -> int:\n"
        b"    def nested() -> int:\n"
        b"        return value\n"
        b"    return nested()\n\n"
        b"async def beta() -> None:\n"
        b"    return None\n"
    )
    stdout = StringIO()
    stderr = StringIO()

    exit_code = try_run_provider_native_owner(
        ["owner-search-stdin", "--asp-provider-id", "py-harness"],
        stdin=json.dumps(_request(source)),
        cwd=Path("."),
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    response = json.loads(stdout.getvalue())
    assert response["projectionCompleteness"] == "complete-owner"
    assert response["requestedProjectionMode"] == "complete-owner"
    assert [
        projection["canonicalItemSelector"]["symbol"]
        for projection in response["projections"]
    ] == [
        "alpha",
        "nested",
        "beta",
    ]
    assert response["projections"][0]["canonicalItemSelector"][
        "structuralSelector"
    ] == ("python://src/example.py#item/function/alpha")
    assert response["projections"][1]["canonicalItemSelector"]["scopes"] == [
        {"relation": "lexical-owner", "kind": "function", "symbol": "alpha"}
    ]
    for projection in response["projections"]:
        projected = source[projection["sourceByteStart"] : projection["sourceByteEnd"]]
        selector = projection["canonicalItemSelector"]
        assert selector["schemaId"] == "asp.canonical-item-selector.v1"
        assert selector["schemaVersion"] == "1"
        assert selector["symbol"].encode() in projected


def test_owner_search_disambiguates_same_method_name_by_class_scope() -> None:
    source = (
        b"class Alpha:\n"
        b"    def render(self) -> str:\n"
        b"        return 'alpha'\n\n"
        b"class Beta:\n"
        b"    def render(self) -> str:\n"
        b"        return 'beta'\n"
    )
    stdout = StringIO()
    stderr = StringIO()
    assert (
        try_run_provider_native_owner(
            ["owner-search-stdin", "--asp-provider-id", "py-harness"],
            stdin=json.dumps(_request(source)),
            cwd=Path("."),
            stdout=stdout,
            stderr=stderr,
        )
        == 0
    )
    methods = [
        projection["canonicalItemSelector"]
        for projection in json.loads(stdout.getvalue())["projections"]
        if projection["canonicalItemSelector"]["kind"] == "method"
    ]
    assert len(methods) == 2
    assert len({method["structuralSelector"] for method in methods}) == 2
    assert {method["scopes"][0]["symbol"] for method in methods} == {"Alpha", "Beta"}
    assert all(method["scopes"][0]["relation"] == "class-owner" for method in methods)


def test_owner_search_rejects_content_digest_drift() -> None:
    request = _request(b"def alpha():\n    return 1\n")
    request["sourceFingerprint"]["contentDigest"] = "0" * 64  # type: ignore[index]
    stdout = StringIO()
    stderr = StringIO()

    exit_code = try_run_provider_native_owner(
        ["owner-search-stdin", "--asp-provider-id", "py-harness"],
        stdin=json.dumps(request),
        cwd=Path("."),
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 2
    assert stdout.getvalue() == ""
    assert "content digest drift" in stderr.getvalue()


def test_cli_and_registry_expose_native_owner_transport() -> None:
    source = b"def graph_turbo_entry():\n    return 1\n"
    stdout = StringIO()
    stderr = StringIO()

    exit_code = run_cli(
        ["owner-search-stdin", "--asp-provider-id", "py-harness"],
        stdin=json.dumps(_request(source)),
        cwd=Path("."),
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    descriptors = {
        descriptor["method"]: descriptor
        for descriptor in python_semantic_language_method_descriptors()
    }
    assert descriptors["search/owner-native"]["invocation"]["argv"] == [
        "py-harness",
        "owner-search-stdin",
        "--asp-provider-id",
        "py-harness",
    ]
