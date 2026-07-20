"""Evidence graph CLI tests for the Python harness provider."""

from __future__ import annotations

import io
import json
from pathlib import Path

from python_lang_project_harness import run_cli


def test_cli_evidence_graph_renders_json_contract(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "evidence-fixture"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        ["evidence", "graph", "--json", str(tmp_path)],
        stdout=stdout,
        cwd=tmp_path,
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["schemaId"] == "agent.semantic-protocols.semantic-evidence-graph"
    assert payload["protocolId"] == "agent.semantic-protocols.evidence-graph"
    assert payload["producer"]["languageId"] == "python"
    assert payload["producer"]["providerId"] == "py-harness"
    assert payload["project"]["package"] == "evidence-fixture"
    assert payload["summary"] == {
        "nodes": 4,
        "edges": 3,
        "owners": 1,
        "claims": 1,
        "staleItems": 0,
        "gaps": 1,
    }
    assert any(node["kind"] == "owner" for node in payload["nodes"])
    assert any(edge["kind"] == "requires-evidence" for edge in payload["edges"])
    assert payload["gaps"][0]["fields"]["nextCommand"] == "py-harness check --full ."


def test_cli_evidence_analyze_renders_graph_turbo_request(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "analysis-fixture"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        ["evidence", "analyze", "--json", str(tmp_path)],
        stdout=stdout,
        cwd=tmp_path,
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert (
        payload["schemaId"] == "agent.semantic-protocols.semantic-graph-turbo-request"
    )
    assert payload["packetKind"] == "graph-turbo-request"
    assert payload["surface"] == "evidence-analyze"
    assert payload["profile"] == "evidence-quality"
    assert payload["producer"]["languageId"] == "python"
    assert payload["summary"]["graphs"] == 1
    assert payload["summary"]["nodes"] == 4
    assert payload["summary"]["gaps"] == 1
    assert payload["graphs"][0]["graphId"] == "python.evidence.graph"
    assert payload["seedIds"] == ["python:owner:pyproject.toml"]
    assert any(
        edge["relation"] == "requires-evidence"
        for edge in payload["graphs"][0]["edges"]
    )


def test_agent_registry_advertises_evidence_methods(tmp_path: Path) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(
        ["agent", "doctor", "--json", str(tmp_path)],
        stdout=stdout,
        cwd=tmp_path,
    )

    assert exit_code == 0
    registry = json.loads(stdout.getvalue())
    language = registry["registry"]["languages"][0]
    assert "evidence/graph" in language["methods"]
    assert "evidence/analyze" in language["methods"]
    analyze = next(
        descriptor
        for descriptor in language["methodDescriptors"]
        if descriptor["method"] == "evidence/analyze"
    )
    assert analyze["command"] == "evidence"
    assert analyze["outputSchemaIds"] == [
        "agent.semantic-protocols.semantic-graph-turbo-request"
    ]


def test_agent_guide_advertises_evidence_commands(tmp_path: Path) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "guide"], stdout=stdout, cwd=tmp_path)

    assert exit_code == 0
    guide = stdout.getvalue()
    assert "evidence graph --json" in guide
    assert "evidence analyze --json" in guide
