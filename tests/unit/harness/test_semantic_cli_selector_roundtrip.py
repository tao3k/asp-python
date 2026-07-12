"""Structural-selector round-trip tests for the Python semantic CLI."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from python_lang_project_harness import run_cli


def test_cli_query_round_trips_parser_owned_structural_selector(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()
    selector = "python://src/pkg/service.py#item/function/fetch"

    exit_code = run_cli(
        [
            "query",
            "--selector",
            selector,
            "--term",
            "fetch",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    packet = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert packet["ownerPath"] == "src/pkg/service.py"
    assert packet["matchMode"] == "exact"
    assert packet["queryCoverage"] == [
        {"value": "fetch", "status": "hit", "match": "exact", "matchCount": 1}
    ]
    assert [match["structuralSelector"] for match in packet["matches"]] == [selector]
    assert packet["matches"][0]["code"].startswith("def fetch()")
