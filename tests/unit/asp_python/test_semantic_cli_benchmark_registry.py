"""Registry benchmark invocation contract tests."""

from asp_python import python_semantic_language_registration


def test_registry_publishes_no_search_orchestration_invocation() -> None:
    descriptors = python_semantic_language_registration()["methodDescriptors"]
    search_descriptors = [
        descriptor
        for descriptor in descriptors
        if descriptor["method"].startswith("search/")
    ]

    assert search_descriptors == []
