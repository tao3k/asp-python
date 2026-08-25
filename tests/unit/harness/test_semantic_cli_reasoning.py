"""Executable reasoning-entry tests for the Python semantic CLI."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from python_lang_project_harness import run_cli


def test_cli_agent_doctor_advertises_reasoning_search(tmp_path: Path) -> None:
    stdout = io.StringIO()

    assert run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout) == 0

    registration = json.loads(stdout.getvalue())["registry"]["languages"][0]
    assert "search/reasoning" in registration["methods"]
    assert any(
        descriptor["method"] == "search/reasoning"
        and descriptor["supportsCompact"] is True
        and descriptor["supportsJson"] is True
        for descriptor in registration["methodDescriptors"]
    )


def test_cli_agent_guide_prints_reasoning_entry_commands(tmp_path: Path) -> None:
    stdout = io.StringIO()

    assert run_cli(["agent", "guide", str(tmp_path)], stdout=stdout) == 0

    rendered = stdout.getvalue()
    assert (
        "|cmd reasoning-owner-tests=asp python search reasoning owner-tests "
        "--owner <owner-path> --workspace <workspace-root> --view seeds"
    ) in rendered
    assert (
        "|cmd reasoning-owner-query=asp python search reasoning owner-query "
        "--owner <owner-path> --query <symbol> --workspace <workspace-root> --view seeds"
    ) in rendered
    assert (
        "|cmd reasoning-query-deps=asp python search reasoning query-deps "
        "--query <symbol> --dependency <pkg> --workspace <workspace-root> --view seeds"
    ) in rendered


def test_cli_search_reasoning_profiles_are_executable(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    owner_tests_stdout = io.StringIO()
    owner_query_stdout = io.StringIO()
    query_deps_stdout = io.StringIO()

    assert (
        run_cli(
            [
                "search",
                "reasoning",
                "owner-tests",
                "--owner",
                "src/pkg/service.py",
                "--workspace",
                str(tmp_path),
            ],
            stdout=owner_tests_stdout,
        )
        == 0
    )
    assert (
        run_cli(
            [
                "search",
                "reasoning",
                "owner-query",
                "--owner",
                "src/pkg/service.py",
                "--query",
                "build",
                "--workspace",
                str(tmp_path),
            ],
            stdout=owner_query_stdout,
        )
        == 0
    )
    assert (
        run_cli(
            [
                "search",
                "reasoning",
                "query-deps",
                "--query",
                "Session",
                "--dependency",
                "requests",
                "--workspace",
                str(tmp_path),
            ],
            stdout=query_deps_stdout,
        )
        == 0
    )

    owner_tests = owner_tests_stdout.getvalue()
    owner_query = owner_query_stdout.getvalue()
    query_deps = query_deps_stdout.getvalue()
    assert owner_tests.startswith("[search-reasoning] profile=owner-tests")
    assert "returns=covering-tests,test-entrypoints,fixtures" in owner_tests
    assert "|hit path=tests/test_service.py" in owner_tests
    assert owner_query.startswith("[search-reasoning] profile=owner-query")
    assert "returns=items,tests,dependency-usage" in owner_query
    assert "|item build" in owner_query
    assert query_deps.startswith("[search-reasoning] profile=query-deps")
    assert "returns=owners,imports,usage-tests" in query_deps
    assert "dependency=requests" in query_deps
