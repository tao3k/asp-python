"""Owner item query tests for the Python semantic CLI."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from python_lang_project_harness import run_cli


def test_cli_search_owner_items_query_returns_compact_code(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()
    json_stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "fetch|build",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )
    json_exit_code = run_cli(
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

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-owner] q=src/pkg/service.py owner=1")
    assert "item=2 itemQuery=fetch|build itemStatus=hit itemMatch=exact" in rendered
    assert "|query itemQuery=fetch|build status=hit match=exact item=2" in rendered
    assert "|item fetch kind=function" in rendered
    assert "public=false" not in rendered
    assert "doc=false" not in rendered
    assert (
        "structuralSelector=python://src/pkg/service.py#item/function/fetch" in rendered
    )
    assert "displayLineRange=" in rendered
    assert "sourceLocatorHint=src/pkg/service.py:" in rendered
    assert "read=src/pkg/service.py:" in rendered
    assert "|item build kind=function" in rendered
    assert "next=query-code" in rendered
    assert "|code " not in rendered
    assert " text=" not in rendered
    assert "    return value.strip()" not in rendered

    packet = json.loads(json_stdout.getvalue())
    assert json_exit_code == 0
    assert packet["items"][0]["name"] == "fetch"
    assert (
        packet["items"][0]["fields"]["structuralSelector"]
        == "python://src/pkg/service.py#item/function/fetch"
    )
    assert packet["items"][0]["fields"]["displayLineRange"]
    assert packet["items"][0]["fields"]["sourceLocatorHint"].startswith(
        "src/pkg/service.py:"
    )
    assert (
        packet["items"][0]["fields"]["code"]
        == "def fetch() -> Response:\n  return Response"
    )
    assert packet["items"][1]["name"] == "build"


def test_cli_search_owner_items_code_flag_returns_pure_compact_code(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "build",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered == "def build(value: str) -> str:\n  return strip\n"
    assert "[search-owner]" not in rendered
    assert "|code" not in rendered


def test_cli_search_owner_items_code_flag_rejects_json(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "build",
            "--code",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 2
    assert "--code cannot be combined with --json" in stderr.getvalue()


def test_cli_search_owner_items_query_miss_returns_owner_top_items(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "missingSymbol",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert "itemStatus=miss" in rendered
    assert "fallback=owner-top-items" in rendered
    assert "|query itemQuery=missingSymbol status=miss" in rendered
    assert "|item SessionClient kind=class" in rendered
    assert (
        "structuralSelector=python://src/pkg/service.py#item/class/SessionClient"
        in rendered
    )
    assert "displayLineRange=" in rendered
    assert "sourceLocatorHint=src/pkg/service.py:" in rendered
    assert "read=src/pkg/service.py:" in rendered


def test_cli_search_owner_items_query_matches_function_body_text(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "strip",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert "itemQuery=strip itemStatus=hit itemMatch=fallback-contains" in rendered
    assert "|item build kind=function" in rendered
    assert (
        "structuralSelector=python://src/pkg/service.py#item/function/build" in rendered
    )
    assert "displayLineRange=" in rendered
    assert "sourceLocatorHint=src/pkg/service.py:" in rendered
    assert "read=src/pkg/service.py:" in rendered
    assert "next=query-code" in rendered
    assert "|code " not in rendered
    assert " text=" not in rendered


def test_cli_query_json_emits_projection_nodes_and_expand_actions(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "service.py").write_text(
        "\n".join(
            [
                "def decide(value: int) -> int:",
                "    if value > 0:",
                "        return value",
                "    return 0",
            ]
        ),
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "src/pkg/service.py",
            "--term",
            "decide",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    packet = json.loads(stdout.getvalue())
    projection = packet["matches"][0]["projection"]
    nodes = projection["nodes"]
    node_ids = {node["id"] for node in nodes}
    assert exit_code == 0
    assert projection["mode"] == "compact"
    assert projection["syntax"] == "save-token-ruff"
    assert projection["compactSafety"] == {
        "literalPolicy": "summarize",
        "whitespacePolicy": "formatter-structural",
        "normalization": "none",
        "alignment": "parser-roundtrip",
        "exactReadRequired": True,
    }
    assert len(node_ids) == len(nodes)
    assert projection["renderedNodeIds"]
    assert set(projection["renderedNodeIds"]).issubset(node_ids)
    rows = projection["renderedRows"]
    assert [row["nodeId"] for row in rows] == projection["renderedNodeIds"]
    assert "\n".join(row["text"] for row in rows) == packet["matches"][0]["code"]
    assert all(
        any(char.isalnum() or char == "_" for char in row["text"]) for row in rows
    )
    assert any(node["read"] != projection["exactRead"] for node in nodes)
    assert all("nativeId" in node for node in nodes)
    assert all("structuralFingerprint" in node for node in nodes)
    assert any(node.get("parentId") not in {None, "decide"} for node in nodes)
    assert all(
        node.get("parentId") in node_ids
        for node in nodes
        if node.get("parentId") is not None
    )
    assert any(
        action.get("target") != "decide"
        and action.get("read") != projection["exactRead"]
        for action in projection["expandActions"]
    )
    for action in projection["expandActions"]:
        if action.get("kind") != "exact-read":
            continue
        assert action["read"].startswith("src/pkg/service.py")

    (tmp_path / "pyproject.toml").write_text(
        '\n[project]\nname = "demo-python"\nversion = "0.1.0"\nimport-names = ["pkg"]\n',
        encoding="utf-8",
    )
