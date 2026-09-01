"""Semantic search ingest CLI parsing tests."""

from __future__ import annotations

import time
from io import StringIO
from pathlib import Path

import pytest

from asp_python import python_semantic_language_registration, run_cli
from asp_python._semantic_search_cli import parse_semantic_search_args

FAST_INGEST_BUDGET_SECONDS = 0.25


def test_search_ingest_descriptor_accepts_items_tests_pipes() -> None:
    descriptors = python_semantic_language_registration()["methodDescriptors"]

    assert any(
        descriptor["method"] == "search/ingest"
        and descriptor["acceptedPipes"] == ["items", "tests"]
        and descriptor["acceptsStdin"] is True
        for descriptor in descriptors
    )


def test_search_ingest_accepts_pipes_with_explicit_workspace() -> None:
    parsed = parse_semantic_search_args(
        ["ingest", "items", "tests", "--view", "seeds", "--workspace", "."]
    )

    assert parsed.error is None
    assert parsed.view == "ingest"
    assert parsed.pipes == ("items", "tests")
    assert parsed.project_root == Path(".")
    assert parsed.render_mode == "seeds"


def test_search_ingest_rejects_positional_workspace_after_pipes() -> None:
    parsed = parse_semantic_search_args(
        ["ingest", "items", "tests", "extra", "--view", "seeds", "."]
    )

    assert (
        parsed.error
        == "search does not accept positional WORKSPACE; use --workspace <workspace-root>"
    )


def test_search_ingest_empty_stdin_seeds_explains_prime_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    from asp_python import _cli_protocol

    def fail_full_harness(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("full harness should not run for empty ingest seeds")

    monkeypatch.setattr(_cli_protocol, "_run_search_harness", fail_full_harness)
    stdout = StringIO()

    started_at = time.perf_counter()
    exit_code = run_cli(
        [
            "search",
            "ingest",
            "items",
            "tests",
            "--view",
            "seeds",
            "--workspace",
            ".",
        ],
        stdout=stdout,
        stdin="",
        cwd=tmp_path,
    )
    elapsed = time.perf_counter() - started_at

    output = stdout.getvalue()
    assert exit_code == 0
    assert output.startswith("[search-ingest]")
    assert "|note kind=stdin-required" in output
    assert "search ingest consumes stdin candidate paths" in output
    assert "search prime --view seeds" in output
    assert "|next prime:" in output
    assert "owner:path(search prime" not in output
    assert elapsed < FAST_INGEST_BUDGET_SECONDS
