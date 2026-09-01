"""Registry and guide tests for Python tree-sitter query support."""

from __future__ import annotations

import io
import json
from pathlib import Path

from asp_python import run_cli


def test_agent_doctor_advertises_tree_sitter_query_descriptor(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout)
    registration = json.loads(stdout.getvalue())["registry"]["languages"][0]

    assert exit_code == 0
    assert "query" in registration["methods"]
    assert any(
        descriptor["method"] == "query"
        and descriptor["grammarId"] == "tree-sitter-python"
        and descriptor["grammarProfilePath"]
        == "tree-sitter/tree-sitter-python/grammar-profile.json"
        and descriptor["packetSchemas"] == ["semantic-tree-sitter-query.v1"]
        and descriptor["queryInputForms"] == ["catalog-id", "s-expression"]
        and descriptor["supportedPredicates"]
        == [
            "#eq?",
            "#any-eq?",
            "#any-of?",
            "#match?",
            "#any-match?",
            "#not-eq?",
            "#not-match?",
        ]
        and descriptor["unsupportedPredicates"] == []
        and all(
            catalog["sourceDelivery"] == "provider-binary-embedded"
            for catalog in descriptor["queryCatalogs"]
        )
        for descriptor in registration["methodDescriptors"]
    )


def test_agent_guide_lists_tree_sitter_query_entrypoint(tmp_path: Path) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "guide", str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    assert (
        "|cmd catalog-json=asp python query --catalog declarations --json --workspace <workspace-root>"
        in stdout.getvalue()
    )
    assert "syntax predicates supported=#eq?,#any-eq?,#any-of?" in stdout.getvalue()
