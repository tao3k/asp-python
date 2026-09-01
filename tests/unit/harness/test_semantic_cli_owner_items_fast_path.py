"""Owner item fast-path tests for the Python semantic CLI."""

from __future__ import annotations

import io
import json
import time
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from asp_python import run_cli

OWNER_ITEMS_WARM_PATH_GATE_MS = 100.0
OWNER_WARM_PATH_GATE_MS = 100.0
DEPENDENCY_WARM_PATH_GATE_MS = 100.0


def test_cli_search_owner_items_query_uses_exact_owner_fast_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_search_fixture(tmp_path)
    json_stdout = io.StringIO()

    def fail_full_harness(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("owner-items should not run the full Python harness")

    from asp_python import _runner

    monkeypatch.setattr(_runner, "run_asp_python", fail_full_harness)

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "fetch|build",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=json_stdout,
    )

    packet = json.loads(json_stdout.getvalue())
    assert exit_code == 0
    assert packet["runtimeCost"]["reason"] == "owner-items-exact-owner-prefilter"
    assert packet["runtimeCost"]["fields"] == {
        "ownerPath": "src/pkg/service.py",
        "paths": 1,
    }
    assert [item["name"] for item in packet["items"]] == ["fetch", "build"]


def test_cli_search_owner_items_query_stays_inside_warm_path_gate(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    args = [
        "search",
        "owner",
        "src/pkg/service.py",
        "items",
        "--query",
        "fetch|build",
        "--json",
        "--workspace",
        str(tmp_path),
    ]

    warmup_stdout = io.StringIO()
    assert run_cli(args, stdout=warmup_stdout) == 0
    assert "owner-items-exact-owner-prefilter" in warmup_stdout.getvalue()

    timed_stdout = io.StringIO()
    started_at = time.perf_counter()
    exit_code = run_cli(args, stdout=timed_stdout)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    assert exit_code == 0
    assert "owner-items-exact-owner-prefilter" in timed_stdout.getvalue()
    assert elapsed_ms < OWNER_ITEMS_WARM_PATH_GATE_MS


def test_cli_search_owner_path_uses_exact_owner_fast_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_search_fixture(tmp_path)
    json_stdout = io.StringIO()

    def fail_full_harness(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("owner path search should not run the full Python harness")

    from asp_python import _runner

    monkeypatch.setattr(_runner, "run_asp_python", fail_full_harness)

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=json_stdout,
    )

    packet = json.loads(json_stdout.getvalue())
    assert exit_code == 0
    assert packet["runtimeCost"]["reason"] == "owner-exact-path-prefilter"
    assert packet["runtimeCost"]["fields"] == {
        "ownerPath": "src/pkg/service.py",
        "paths": 1,
    }
    assert [owner["path"] for owner in packet["owners"]] == ["src/pkg/service.py"]


def test_cli_search_owner_path_stays_inside_warm_path_gate(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    args = [
        "search",
        "owner",
        "src/pkg/service.py",
        "--json",
        "--workspace",
        str(tmp_path),
    ]

    warmup_stdout = io.StringIO()
    assert run_cli(args, stdout=warmup_stdout) == 0
    assert "owner-exact-path-prefilter" in warmup_stdout.getvalue()

    timed_stdout = io.StringIO()
    started_at = time.perf_counter()
    exit_code = run_cli(args, stdout=timed_stdout)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    assert exit_code == 0
    assert "owner-exact-path-prefilter" in timed_stdout.getvalue()
    assert elapsed_ms < OWNER_WARM_PATH_GATE_MS


def test_cli_search_owner_seed_view_uses_text_fast_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()

    def fail_full_harness(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("owner seed view should not run the full Python harness")

    from asp_python import _cli_protocol

    monkeypatch.setattr(_cli_protocol, "_run_search_harness", fail_full_harness)

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "--view",
            "seeds",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-owner]")
    assert "alg=fast-exact-owner-frontier" in rendered
    assert "O=owner:path(src/pkg/service.py)!owner" in rendered
    assert (
        "entries=owner-tests(O=>covering-tests+test-entrypoints+fixtures)" in rendered
    )


def test_cli_search_dependency_uses_metadata_fast_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write_search_fixture(tmp_path)
    json_stdout = io.StringIO()

    def fail_full_harness(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("dependency search should not run the full Python harness")

    from asp_python import _runner

    monkeypatch.setattr(_runner, "run_asp_python", fail_full_harness)

    exit_code = run_cli(
        [
            "search",
            "deps",
            "requests",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=json_stdout,
    )

    packet = json.loads(json_stdout.getvalue())
    assert exit_code == 0
    assert packet["runtimeCost"]["reason"] == "dependency-metadata-prefilter"
    assert packet["runtimeCost"]["fields"] == {
        "dependency": "requests",
        "paths": 0,
    }
    assert [node["id"] for node in packet["nodes"]] == ["D:requests"]


def test_cli_search_dependency_stays_inside_warm_path_gate(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    args = [
        "search",
        "deps",
        "requests",
        "--json",
        "--workspace",
        str(tmp_path),
    ]

    warmup_stdout = io.StringIO()
    assert run_cli(args, stdout=warmup_stdout) == 0
    assert "dependency-metadata-prefilter" in warmup_stdout.getvalue()

    timed_stdout = io.StringIO()
    started_at = time.perf_counter()
    exit_code = run_cli(args, stdout=timed_stdout)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    assert exit_code == 0
    assert "dependency-metadata-prefilter" in timed_stdout.getvalue()
    assert elapsed_ms < DEPENDENCY_WARM_PATH_GATE_MS
