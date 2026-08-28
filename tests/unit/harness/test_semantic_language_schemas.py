"""Provider-owned schema registration tests for the Python provider."""

from __future__ import annotations

from python_lang_project_harness import python_semantic_language_registration


def test_python_registration_advertises_only_provider_owned_schemas() -> None:
    registration = python_semantic_language_registration()

    assert registration["schemas"] == [
        {
            "schemaId": "agent.semantic-protocols.languages.python.asp-python.capabilities",
            "schemaVersion": "1",
            "path": "schemas/python-semantic-capabilities.v1.schema.json",
        }
    ]


def test_python_registration_does_not_advertise_shared_schema_ids() -> None:
    registration = python_semantic_language_registration()
    provider_owned_schema_ids = {
        "agent.semantic-protocols.languages.python.asp-python.capabilities"
    }
    advertised_schema_ids = {schema["schemaId"] for schema in registration["schemas"]}

    assert advertised_schema_ids - provider_owned_schema_ids == set()
