"""Semantic CLI protocol tests for the Python harness provider."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from python_lang_project_harness import python_semantic_language_registration, run_cli


def test_cli_agent_doctor_json_advertises_semantic_language_provider(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    registration = payload["languages"][0]
    assert registration["languageId"] == "python"
    assert registration["providerId"] == "py-harness"
    assert registration["binary"] == "py-harness"
    assert registration["namespace"] == (
        "agent.semantic-protocols.languages.python.py-harness"
    )
    assert any(
        schema["schemaId"] == "agent.semantic-protocols.semantic-graph"
        and schema["path"] == "schemas/semantic-graph.v1.schema.json"
        for schema in registration["schemas"]
    )
    assert any(
        schema["schemaId"] == "agent.semantic-protocols.semantic-type-surface"
        and schema["path"] == "schemas/semantic-type-surface.v1.schema.json"
        for schema in registration["schemas"]
    )
    assert any(
        schema["schemaId"] == "agent.semantic-protocols.dev-command-log"
        and schema["path"] == "schemas/semantic-dev-command-log.v1.schema.json"
        for schema in registration["schemas"]
    )
    assert "search/workspace" in registration["methods"]
    assert "search/callsite" in registration["methods"]
    assert "search/public-external-types" in registration["methods"]
    assert "search/lexical" in registration["methods"]
    assert "agent/doctor" in registration["methods"]
    assert "agent/guide" in registration["methods"]
    assert "agent/install" not in registration["methods"]
    assert "agent/hook" not in registration["methods"]
    assert any(
        descriptor["method"] == "search/public-external-types"
        and descriptor["outputSchemaIds"]
        == [
            "agent.semantic-protocols.semantic-search-packet",
            "agent.semantic-protocols.semantic-type-surface",
        ]
        for descriptor in registration["methodDescriptors"]
    )
    assert any(
        descriptor["method"] == "search/lexical"
        and descriptor["acceptedPipes"] == ["owner", "tests"]
        and descriptor["supportsQuerySet"] is True
        and descriptor["acceptedQuerySetSelectors"] == ["lexical-set"]
        and descriptor["querySetScopes"] == ["project", "owner"]
        for descriptor in registration["methodDescriptors"]
    )
    assert any(
        descriptor["method"] == "search/owner"
        and descriptor["acceptedPipes"] == ["items"]
        and any(
            capability["name"] == "python-owner-item-query"
            for capability in descriptor["capabilities"]
        )
        and descriptor["fallbacks"][0]["name"] == "owner-top-items"
        for descriptor in registration["methodDescriptors"]
    )
    assert not any(
        descriptor["method"] in {"agent/install", "agent/hook"}
        for descriptor in registration["methodDescriptors"]
    )
    assert any(
        descriptor["method"] == "agent/guide"
        and descriptor["command"] == "agent"
        and descriptor["supportsCompact"] is True
        and descriptor["supportsJson"] is False
        for descriptor in registration["methodDescriptors"]
    )


def test_cli_agent_guide_prints_provider_owned_searchflow(tmp_path: Path) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "guide", str(tmp_path)], stdout=stdout)

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith(f"[py-harness-guide] project={tmp_path}")
    assert (
        "|catalog reasoningProfiles=owner-query,query-deps,owner-tests,"
        "finding-frontier,feature-cfg entries=owner-query,query-deps,owner-tests "
        "routes=read-frontier,syntax-locate,syntax-code,query-code"
    ) in rendered
    assert (
        "|routing evidence-state prime=owner-map-only pipe=ambiguous-query" in rendered
    )
    assert (
        "|route syntax-locate selectors=S:tree-sitter-query,Scope:owner-or-structural "
        "returns=locator,capture,frontier code=false"
    ) in rendered
    assert "<path[:line|:start-end]>" not in rendered
    assert "displayLineRange/sourceLocatorHint are display hints" in rendered
    assert (
        "|route syntax-code selectors=S:tree-sitter-query,R:exact-selector "
        "returns=code code=pure"
    ) in rendered
    assert "|route query-code selectors=O:owner,Q:symbol" in rendered
    assert (
        "|cmd prime=asp python search prime --workspace <workspace-root> --view seeds"
        in rendered
    )
    assert f"|cmd asp python search prime --view seeds {tmp_path}" not in rendered
    assert (
        "|cmd owner=asp python search owner <owner-path> --workspace <workspace-root> --view seeds"
        in rendered
    )
    assert "asp python search owner <owner-path> items --query <symbol|a|b>" in rendered
    assert (
        "asp python query --from-hook owner-local-projection --selector <selector> "
        "--term <term> --surface owners,tests --workspace <workspace-root> --view seeds"
        in rendered
    )
    assert (
        "|cmd syntax-code=asp python query --treesitter-query "
        "'(function_definition name: (identifier) @function.name)' "
        "--selector <exact-structural-selector> --workspace <workspace-root> --code"
    ) in rendered
    assert (
        "|cmd query-code=asp python query <owner-path> --term <symbol> "
        "--workspace <workspace-root> --code"
    ) in rendered
    assert (
        "|rule selector queries do not need a trailing project root; "
        "--workspace <workspace-root> is the independent workspace override"
    ) in rendered
    assert "trailing . is the project root" not in rendered
    assert "--code --workspace" not in rendered
    assert (
        "asp python search lexical <query> owner tests "
        "--workspace <workspace-root> --view seeds"
    ) in rendered
    assert "--view metadata is document-only for asp md/org query" in rendered
    assert "query <owner-path> --term <symbol> --code|--names-only" in rendered
    assert "|rule use the asp python facade" in rendered


def test_python_capability_schema_covers_registry_descriptors() -> None:
    schema_path = (
        Path(__file__).resolve().parents[3]
        / "schemas"
        / "python-semantic-capabilities.v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    capability_names = set(
        schema["$defs"]["capabilityDescriptor"]["properties"]["name"]["enum"]
    )
    ingest_names = set(
        schema["$defs"]["ingestSurfaceDescriptor"]["properties"]["name"]["enum"]
    )

    for descriptor in python_semantic_language_registration()["methodDescriptors"]:
        for capability in descriptor.get("capabilities", []):
            assert capability["name"] in capability_names
        for ingest_surface in descriptor.get("ingestRequiredFor", []):
            assert ingest_surface["name"] in ingest_names


def test_cli_search_knowledge_axes_accept_multi_term_queries(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'demo'\ndependencies = ['pytest']\n",
        encoding="utf-8",
    )

    cases = [
        (["search", "compare", "ast", "tokenize"], "search/compare", "ast tokenize"),
        (
            ["search", "extension", "pytest", "fixture"],
            "search/extension",
            "pytest fixture",
        ),
        (
            ["search", "pattern", "dependency", "api"],
            "search/pattern",
            "dependency api",
        ),
    ]
    for argv, expected_method, expected_query in cases:
        stdout = io.StringIO()
        exit_code = run_cli(
            [*argv, "--json", "--workspace", str(tmp_path)],
            stdout=stdout,
        )

        assert exit_code == 0
        packet = json.loads(stdout.getvalue())
        assert packet["method"] == expected_method
        assert packet["query"] == expected_query
        assert packet["header"]["fields"]["evidenceGrade"] == "fact"


def test_cli_search_callsite_uses_parser_call_facts(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        ["search", "callsite", "build", "--workspace", str(tmp_path)],
        stdout=stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-callsite] q=build hit=1")
    assert "|owner tests/test_service.py" in rendered
    assert "|hit path=tests/test_service.py line=4" in rendered
    assert "kind=callsite" in rendered
    assert "symbol=build" in rendered


def test_cli_search_deps_routes_dependency_api_followups(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()
    json_stdout = io.StringIO()

    exit_code = run_cli(
        ["search", "deps", "requests@2::Session", "--workspace", str(tmp_path)],
        stdout=stdout,
    )
    json_exit_code = run_cli(
        [
            "search",
            "deps",
            "requests@2::Session",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=json_stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-deps] q=requests@2::Session")
    assert "package=requests" in rendered
    assert "requestedVersion=2" in rendered
    assert "versionScope=current" in rendered
    assert "api=Session" in rendered
    assert (
        "|next dependency:requests,public-external-types:requests,"
        "api:requests@2::Session,text:Session,tests:Session"
    ) in rendered

    packet = json.loads(json_stdout.getvalue())
    assert json_exit_code == 0
    assert packet["method"] == "search/deps"
    assert packet["header"]["kind"] == "search-deps"
    assert packet["header"]["fields"]["package"] == "requests"
    assert packet["header"]["fields"]["api"] == "Session"
    assert {action["kind"] for action in packet["nextActions"]} >= {
        "dependency",
        "public-external-types",
        "api",
        "text",
        "tests",
    }


def test_cli_search_ingest_groups_rg_output_by_owner(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        ["search", "ingest", "--workspace", str(tmp_path)],
        stdout=stdout,
        stdin="src/pkg/service.py:3:def build(value: str) -> str:\n",
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-ingest] source=rg-n hit=1")
    assert "|owner src/pkg/service.py" in rendered
    assert "|hit path=src/pkg/service.py line=3" in rendered
