"""Semantic CLI protocol tests for the Python harness provider."""

from __future__ import annotations

import io
import json
from pathlib import Path

from asp_python import python_semantic_language_registration, run_cli


def test_cli_agent_doctor_advertises_provider(tmp_path: Path) -> None:
    stdout = io.StringIO()
    assert run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout) == 0
    registration = json.loads(stdout.getvalue())["registry"]["languages"][0]
    assert registration["languageId"] == "python"
    assert registration["providerId"] == "asp-python"
    assert "query/exact-selector-native-v1" in registration["methods"]


def test_cli_agent_guide_uses_asp_owned_exact_projection(tmp_path: Path) -> None:
    stdout = io.StringIO()
    assert run_cli(["agent", "guide", str(tmp_path)], stdout=stdout) == 0
    rendered = stdout.getvalue()
    assert "routes=syntax-locate,exact-source,callable-skeleton" in rendered
    assert "|route exact-source selectors=R:exact-selector returns=source" in rendered
    assert "|route callable-skeleton selectors=R:exact-callable-selector" in rendered
    assert "no raw Python source reads" in rendered


def test_search_descriptors_publish_benchmark_invocations() -> None:
    descriptors = python_semantic_language_registration()["methodDescriptors"]
    assert all(
        descriptor["method"] != "search/owner-native" for descriptor in descriptors
    )
    exact = next(
        descriptor
        for descriptor in descriptors
        if descriptor["method"] == "query/exact-selector-native-v1"
    )
    assert exact["invocation"]["argv"][:3] == ["asp", "python", "query"]
