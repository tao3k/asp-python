"""Semantic CLI query-set core protocol tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import (
    compact_graph_renderer_available,
    write_search_fixture,
)

from python_lang_project_harness import run_cli


def test_cli_search_text_query_set_and_flag_like_literal_query(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    query_set_stdout = io.StringIO()
    query_set_json_stdout = io.StringIO()
    flag_like_stdout = io.StringIO()

    query_set_exit = run_cli(
        [
            "search",
            "lexical",
            "--query",
            "build",
            "--query",
            "Session",
            "owner",
            "tests",
            "--owner",
            "src/pkg/service.py",
            "--workspace",
            str(tmp_path),
        ],
        stdout=query_set_stdout,
    )
    query_set_json_exit = run_cli(
        [
            "search",
            "lexical",
            "--query",
            "build",
            "--query",
            "Session",
            "owner",
            "tests",
            "--owner",
            "src/pkg/service.py",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=query_set_json_stdout,
    )
    flag_like_exit = None
    if compact_graph_renderer_available():
        flag_like_exit = run_cli(
            [
                "search",
                "lexical",
                "--json",
                "--view",
                "seeds",
                "--workspace",
                str(tmp_path),
            ],
            stdout=flag_like_stdout,
        )

    rendered = query_set_stdout.getvalue()
    assert query_set_exit == 0
    assert rendered.startswith('[search-lexical] q="build,Session" querySet=2')
    assert "selector=lexical-set" in rendered
    assert "scopeOwner=src/pkg/service.py" in rendered
    assert "|query build " in rendered
    assert "|query Session " in rendered
    assert "queryTerms=build" in rendered
    assert "queryTerms=Session" in rendered
    assert "|synthesis " in rendered
    assert "editFrontier=src/pkg/service.py" in rendered
    assert "windowSet=owner:src/pkg/service.py" in rendered
    assert "|seed owner:src/pkg/service.py" in rendered
    assert "|next owner:src/pkg/service.py,tests:src/pkg/service.py" in rendered
    for line in rendered.splitlines():
        if line.startswith("|seed "):
            assert ",owner:" not in line
            assert ",tests:" not in line
    assert "|edge O:src/pkg/service.py -test-> O:tests/test_service.py" in rendered

    packet = json.loads(query_set_json_stdout.getvalue())
    assert query_set_json_exit == 0
    assert packet["query"] == "build,Session"
    assert [term["value"] for term in packet["querySet"]] == ["build", "Session"]
    assert packet["queryComposition"]["mode"] == "query-set"
    assert packet["queryComposition"]["selector"] == "lexical-set"
    assert packet["queryComposition"]["merge"] == [
        "nodes",
        "edges",
        "owners",
        "hits",
        "typeSurfaces",
        "nextActions",
        "notes",
    ]
    assert packet["queryComposition"]["scope"]["ownerPath"] == "src/pkg/service.py"
    assert packet["header"]["fields"]["querySet"] == 2
    assert packet["header"]["fields"]["selector"] == "lexical-set"
    assert packet["header"]["fields"]["scopeOwner"] == "src/pkg/service.py"
    assert [query["value"] for query in packet["queryCoverage"]] == [
        "build",
        "Session",
    ]
    assert all(query["hitCount"] > 0 for query in packet["queryCoverage"])
    assert packet["ownerResolution"] == [
        {
            "target": "src/pkg/service.py",
            "status": "workspace-owner",
            "realOwner": True,
            "ownerPath": "src/pkg/service.py",
            "reason": "parser-visible owner selected by lexical search",
        }
    ]
    assert packet["searchSynthesis"]["seeds"] == [
        {"kind": "owner", "target": "src/pkg/service.py"}
    ]
    assert packet["searchSynthesis"]["windowSet"] == [
        {"kind": "owner", "target": "src/pkg/service.py"}
    ]
    assert packet["searchSynthesis"]["editFrontier"] == ["src/pkg/service.py"]
    assert "testFrontier" not in packet["searchSynthesis"]
    assert "runtimeCost" not in packet
    assert "|runtime " not in rendered

    if compact_graph_renderer_available():
        assert flag_like_exit == 0
        assert flag_like_stdout.getvalue().startswith("[search-lexical] q=--json")
