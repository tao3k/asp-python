"""Focused contract tests for the ASP projection-batch provider adapter."""

from __future__ import annotations

import json

from python_lang_project_harness._cli import run_cli


def test_projection_batch_projects_canonical_python_items(capsys: object) -> None:
    source = b"class Agent:\n    def run(self):\n        return 1\n\ndef top():\n    return 2\n"
    header = {
        "schemaId": "asp.provider-language-projection-batch-request.v1",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "py-harness",
        "workspaceIdentity": "workspace-test",
        "transport": "framed-stdin-v1",
        "generationRootDigest": "generation-test",
        "parserIdentityDigest": "parser-test",
        "queryPackDigest": "query-pack-test",
        "baseGenerationRootDigest": None,
        "owners": [
            {
                "ownerPath": "src/example.py",
                "sourceLeafDigest": "source-test",
                "byteLength": len(source),
            }
        ],
    }
    header_bytes = json.dumps(header, separators=(",", ":")).encode()
    frame = len(header_bytes).to_bytes(4, "big") + header_bytes + source

    assert run_cli(["projection-batch-stdin"], stdin=frame) == 0
    response = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]

    assert response["schemaId"] == "asp.provider-language-projection-batch-response.v1"
    assert response["generationRootDigest"] == "generation-test"
    owner = response["owners"][0]
    assert owner["sourceLeafDigest"] == "source-test"
    assert [item["selector"] for item in owner["items"]] == [
        "python://src/example.py#item/class/Agent",
        "python://src/example.py#item/method/run/scope/implementation-owner/type/Agent",
        "python://src/example.py#item/function/top",
    ]
    assert all(
        item["sourceByteStart"] < item["sourceByteEnd"] for item in owner["items"]
    )
    assert owner["items"][0]["projections"] == []
    for item in owner["items"][1:]:
        assert item["projections"][0]["projectionKind"] == "callable-skeleton"
        assert (
            item["projections"][0]["payload"]["schemaId"]
            == "agent.semantic-protocols.callable-skeleton-projection"
        )
