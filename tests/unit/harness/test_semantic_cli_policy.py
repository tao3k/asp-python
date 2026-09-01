from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import compact_graph_renderer_available

from asp_python._cli import run_cli


def test_cli_agent_doctor_json_advertises_policy_search(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()
    exit_code = run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout)
    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    registration = payload["registry"]["languages"][0]
    assert "search/policy" in registration["methods"]
    assert all(
        schema["schemaId"] != "agent.semantic-protocols.semantic-handle"
        for schema in registration["schemas"]
    )
    assert any(
        descriptor["method"] == "search/policy"
        and descriptor["acceptedPipes"] == ["owner", "tests"]
        and descriptor["outputSchemaIds"]
        == [
            "agent.semantic-protocols.semantic-search-packet",
            "agent.semantic-protocols.semantic-handle",
        ]
        and any(
            capability["name"] == "python-project-policy-rule-handle-search"
            for capability in descriptor["capabilities"]
        )
        for descriptor in registration["methodDescriptors"]
    )


def test_cli_search_policy_renders_semantic_handles(
    tmp_path: Path,
) -> None:
    seeds_stdout = io.StringIO()
    compact_stdout = io.StringIO()
    json_stdout = io.StringIO()
    if compact_graph_renderer_available():
        assert (
            run_cli(
                [
                    "search",
                    "policy",
                    "PY-AGENT-PROJECT-001",
                    "owner",
                    "tests",
                    "--view",
                    "seeds",
                    "--workspace",
                    str(tmp_path),
                ],
                stdout=seeds_stdout,
            )
            == 0
        )
    assert (
        run_cli(
            [
                "search",
                "policy",
                "src layout",
                "owner",
                "tests",
                "--workspace",
                str(tmp_path),
            ],
            stdout=compact_stdout,
        )
        == 0
    )
    assert (
        run_cli(
            [
                "search",
                "policy",
                "PY-AGENT-POLICY-008",
                "owner",
                "tests",
                "--json",
                "--workspace",
                str(tmp_path),
            ],
            stdout=json_stdout,
        )
        == 0
    )
    seeds = seeds_stdout.getvalue()
    compact = compact_stdout.getvalue()
    packet = json.loads(json_stdout.getvalue())
    if compact_graph_renderer_available():
        assert seeds.startswith("[search-policy] q=PY-AGENT-PROJECT-001")
        assert "alg=policy-handle-catalog" in seeds
        assert "O=owner:path(src/asp_python/_project_policy_catalog.py)!owner" in seeds
        assert "tests/unit/harness/project_policy/test_layout.py" in seeds
    assert (
        "|handle PY-AGENT-PROJECT-001 kind=policy-rule source=provider-policy"
        in compact
    )
    assert 'title="Python project should use src layout"' in compact
    assert "implementation=None" not in compact
    assert packet["view"] == "policy"
    assert packet["semanticHandles"][0]["id"] == "PY-AGENT-POLICY-008"
    assert packet["semanticHandles"][0]["ownerPath"] == (
        "src/asp_python/_agent_policy_catalog.py"
    )
    assert (
        "tests/unit/harness/test_agent_policy.py"
        in packet["semanticHandles"][0]["testPaths"]
    )
