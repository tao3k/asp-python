"""Semantic CLI workspace search protocol tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from asp_python import run_cli


def test_cli_search_workspace_prime_and_text_pipe(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)

    workspace_stdout = io.StringIO()
    prime_stdout = io.StringIO()
    prime_json_stdout = io.StringIO()
    owner_stdout = io.StringIO()
    owner_json_stdout = io.StringIO()
    text_stdout = io.StringIO()

    assert (
        run_cli(
            ["search", "workspace", "--workspace", str(tmp_path)],
            stdout=workspace_stdout,
        )
        == 0
    )
    assert (
        run_cli(["search", "prime", "--workspace", str(tmp_path)], stdout=prime_stdout)
        == 0
    )
    assert (
        run_cli(
            ["search", "prime", "--json", "--workspace", str(tmp_path)],
            stdout=prime_json_stdout,
        )
        == 0
    )
    assert (
        run_cli(
            ["search", "owner", "src/pkg/service.py", "--workspace", str(tmp_path)],
            stdout=owner_stdout,
        )
        == 0
    )
    assert (
        run_cli(
            [
                "search",
                "owner",
                "src/pkg/service.py",
                "--json",
                "--workspace",
                str(tmp_path),
            ],
            stdout=owner_json_stdout,
        )
        == 0
    )
    assert (
        run_cli(
            [
                "search",
                "lexical",
                "build",
                "owner",
                "tests",
                "--workspace",
                str(tmp_path),
            ],
            stdout=text_stdout,
        )
        == 0
    )

    workspace = workspace_stdout.getvalue()
    prime = prime_stdout.getvalue()
    owner = owner_stdout.getvalue()
    text = text_stdout.getvalue()
    assert workspace.startswith("[search-workspace]")
    assert "|package . name=demo-python role=workspace-root" in workspace
    assert (
        "|package src/pkg name=pkg role=workspace-package surface=source" in workspace
    )
    assert prime.startswith("[search-prime]")
    assert '|dependency D:requests requirement="requests>=2"' in prime
    assert "|owner src/pkg/service.py" in prime
    assert "|synthesis algorithm=owner-rank-frontier scope=prime" in prime
    assert "highImpactOwners=" in prime
    assert "src/pkg/service.py" in prime
    assert "text:build(owner=" in prime
    assert prime.count("deps:requests") == 1
    assert "symbol:build" not in prime
    prime_packet = json.loads(prime_json_stdout.getvalue())
    assert prime_packet["searchSynthesis"]["algorithm"] == "owner-rank-frontier"
    assert prime_packet["searchSynthesis"]["scope"] == "prime"
    assert "src/pkg/service.py" in prime_packet["searchSynthesis"]["highImpactOwners"]
    assert owner.startswith("[search-owner] q=src/pkg/service.py")
    assert "|synthesis algorithm=bounded-reachability-depth1 scope=owner" in owner
    assert "ownerPath=src/pkg/service.py" in owner
    owner_packet = json.loads(owner_json_stdout.getvalue())
    assert owner_packet["searchSynthesis"]["algorithm"] == "bounded-reachability-depth1"
    assert owner_packet["searchSynthesis"]["scope"] == "owner"
    assert owner_packet["searchSynthesis"]["ownerPath"] == "src/pkg/service.py"
    assert owner_packet["searchSynthesis"]["incomingOwners"] >= 1
    assert text.startswith("[search-lexical] q=build")
    assert "|owner src/pkg/service.py" in text
    assert "|edge O:src/pkg/service.py -test-> O:tests/test_service.py" in text


def test_cli_search_workspace_seeds_uses_metadata_route(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)

    stdout = io.StringIO()
    assert (
        run_cli(
            ["search", "workspace", "--view", "seeds", "--workspace", str(tmp_path)],
            stdout=stdout,
        )
        == 0
    )

    workspace = stdout.getvalue()
    assert workspace.startswith("[search-workspace]")
    assert (
        "|note kind=runtime-prefilter message=workspace-seed-metadata-route"
        in workspace
    )


def test_cli_search_deps_exposes_manifest_topology_only(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)

    deps_stdout = io.StringIO()
    assert (
        run_cli(
            ["search", "deps", "requests", "--workspace", str(tmp_path)],
            stdout=deps_stdout,
        )
        == 0
    )

    deps = deps_stdout.getvalue()
    assert deps.startswith("[search-deps] q=requests")
    assert "manifest=1" in deps
    assert "usage=0" in deps
    assert "topology=asp-owned" in deps
    assert '|dependency D:requests requirement="requests>=2"' in deps
    assert "|owner src/pkg/service.py" not in deps
    assert "|hit path=src/pkg/service.py" not in deps
