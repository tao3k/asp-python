"""Registry benchmark invocation contract tests."""

from python_lang_project_harness import python_semantic_language_registration


def test_registered_search_methods_publish_public_benchmark_invocations() -> None:
    descriptors = python_semantic_language_registration()["methodDescriptors"]
    search_descriptors = [
        descriptor
        for descriptor in descriptors
        if descriptor["method"].startswith("search/")
    ]

    assert search_descriptors
    for descriptor in search_descriptors:
        invocation = descriptor["benchmarkInvocation"]
        assert invocation["args"][:2] == ["search", descriptor["view"]]
        assert "{workspace}" in invocation["args"]
        assert isinstance(invocation["expectsJson"], bool)
        assert invocation["maxElapsedMs"] > 0
