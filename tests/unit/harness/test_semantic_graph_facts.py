"""Validate provider-owned Python graph facts."""

from __future__ import annotations

import io
import json

from python_lang_project_harness import run_cli


def test_search_semantic_facts_emits_field_type_collection_graph(tmp_path):
    source = tmp_path / "models.py"
    source.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass\n"
        "class Bag:\n"
        "    items: list[str]\n"
        "    counts: dict[str, int]\n\n"
        "class Runtime:\n"
        "    def __init__(self):\n"
        "        self.values: list[int] = []\n",
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "semantic-facts",
            "list collection fields",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
        cwd=tmp_path,
        stdin="models.py:5:1:items\n",
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["schemaId"] == "agent.semantic-protocols.semantic-fact-graph"
    assert payload["languageId"] == "python"
    assert payload["providerId"] == "asp-python"
    assert payload["query"] == "list collection fields"
    nodes = payload["nodes"]
    edges = payload["edges"]
    assert any(
        node["kind"] == "field"
        and node["symbol"] == "items"
        and node["fields"]["typeValue"] == "list[str]"
        and node["fields"]["collectionKind"] == "list"
        and node["fields"]["languageId"] == "python"
        and node["fields"]["providerId"] == "asp-python"
        and node["fields"]["semanticFactKind"] == "field"
        and node["fields"]["provenance"] == "parser"
        and node["fields"]["confidence"] == "exact"
        and node["fields"]["freshness"] == "fresh"
        and node["fields"]["collectionFamily"] == "sequence"
        and node["fields"]["collectionImpl"] == "list"
        and node["fields"]["field"]["ownerKind"] == "class"
        and node["fields"]["field"]["name"] == "items"
        and node["fields"]["field"]["ownerPath"] == "models.py"
        and "append" in node["fields"]["field"]["access"]
        and node["fields"]["contextLocator"] == "models.py:4:6"
        for node in nodes
    )
    assert any(
        node["kind"] == "type"
        and node["value"] == "list[str]"
        and node["fields"]["semanticFactKind"] == "type"
        and node["fields"]["type"]["name"] == "list[str]"
        and node["fields"]["type"]["element"] == "str"
        for node in nodes
    )
    assert any(
        node["kind"] == "collection"
        and node["symbol"] == "list"
        and node["fields"]["semanticFactKind"] == "collection"
        and node["fields"]["collection"]["family"] == "sequence"
        and node["fields"]["collection"]["impl"] == "list"
        and node["fields"]["collection"]["elementType"] == "str"
        for node in nodes
    )
    assert any(
        node["kind"] == "field"
        and node["symbol"] == "counts"
        and node["fields"]["collectionFamily"] == "map"
        and node["fields"]["field"]["access"] == ["read", "write", "validate"]
        for node in nodes
    )
    assert any(
        node["kind"] == "type"
        and node["value"] == "dict[str, int]"
        and node["fields"]["type"]["key"] == "str"
        and node["fields"]["type"]["value"] == "int"
        for node in nodes
    )
    assert any(
        node["kind"] == "collection"
        and node["symbol"] == "dict"
        and node["fields"]["collection"]["family"] == "map"
        and node["fields"]["collection"]["keyType"] == "str"
        and node["fields"]["collection"]["valueType"] == "int"
        for node in nodes
    )
    assert any(edge["relation"] == "has_type" for edge in edges)
    assert any(edge["relation"] == "collection_of" for edge in edges)


def test_search_semantic_facts_emits_package_build_dependency_and_tests(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'name = "fact-pkg"\n'
        'version = "0.1.0"\n'
        'dependencies = ["requests>=2", "attrs"]\n'
        "\n"
        "[project.optional-dependencies]\n"
        'dev = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    (tmp_path / "model.py").write_text(
        "class Cache:\n    entries: list[str]\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_api.py").write_text(
        "def test_one():\n    assert True\n\ndef helper():\n    pass\n",
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "semantic-facts",
            "field pytest requests dependency",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
        cwd=tmp_path,
        stdin="model.py:2:1:entries\n",
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    nodes = payload["nodes"]
    edges = payload["edges"]
    assert any(
        node["kind"] == "package"
        and node["value"] == "fact-pkg"
        and node["action"] == "package"
        and node["fields"]["semanticFactKind"] == "package"
        and node["fields"]["manifestPath"] == "pyproject.toml"
        for node in nodes
    )
    assert any(
        node["kind"] == "build"
        and node["action"] == "build"
        and node["fields"]["semanticFactKind"] == "build"
        and node["fields"]["command"] == "uv run --project . pytest"
        for node in nodes
    )
    assert any(
        node["kind"] == "dependency"
        and node["value"] == "requests"
        and node["action"] == "deps"
        and node["fields"]["semanticFactKind"] == "dependency"
        and node["fields"]["dependencyKind"] == "normal"
        and node["fields"]["versionReq"] == ">=2"
        for node in nodes
    )
    assert any(
        node["kind"] == "dependency"
        and node["value"] == "pytest"
        and node["fields"]["dependencyKind"] == "dev"
        and node["fields"]["extra"] == "dev"
        for node in nodes
    )
    assert any(
        node["kind"] == "test"
        and node["path"] == "tests/test_api.py"
        and node["action"] == "tests"
        and node["fields"]["semanticFactKind"] == "test"
        and node["fields"]["functionCount"] == 1
        for node in nodes
    )
    for relation in ["builds", "depends_on", "tests", "belongs_to"]:
        assert any(edge["relation"] == relation for edge in edges), relation
    field_node = next(
        node
        for node in nodes
        if node["kind"] == "field" and node["symbol"] == "entries"
    )
    package_node = next(node for node in nodes if node["kind"] == "package")
    assert any(
        edge["source"] == field_node["id"]
        and edge["target"] == package_node["id"]
        and edge["relation"] == "belongs_to"
        for edge in edges
    )
