"""Focused contract tests for the ASP projection-batch provider adapter."""

from __future__ import annotations

from asp_python._projection_batch import project_projection_batch


def test_projection_batch_projects_canonical_python_items() -> None:
    source = "class Agent:\n    def run(self):\n        return 1\n\ndef top():\n    return 2\n"
    request = {
        "schemaId": "agent.semantic-protocols.provider-language-projection-batch-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "workspaceIdentity": "workspace-test",
        "generationRootDigest": "generation-test",
        "parserIdentityDigest": "parser-test",
        "queryPackDigest": "query-pack-test",
        "baseGenerationRootDigest": None,
        "owners": [
            {
                "ownerPath": "src/example.py",
                "sourceLeafDigest": "source-test",
                "sourceEncoding": "utf8",
                "sourceText": source,
            }
        ],
        "auxiliaryOwners": [
            {
                "ownerPath": "pyproject.toml",
                "sourceLeafDigest": "config-test",
                "sourceEncoding": "utf8",
                "sourceText": "[project]\nname = 'fixture'\n",
            }
        ],
    }
    response = project_projection_batch(request)

    assert (
        response["schemaId"]
        == "agent.semantic-protocols.provider-language-projection-batch-response"
    )
    assert response["generationRootDigest"] == "generation-test"
    owner = response["owners"][0]
    assert len(response["owners"]) == 1
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
        payload = item["projections"][0]["payload"]
        assert "schemaId" not in payload
        assert "schemaVersion" not in payload
        assert "projectionKind" not in payload
