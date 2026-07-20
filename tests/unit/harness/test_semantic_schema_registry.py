"""Schema registry contract tests for the Python semantic provider."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_package_local_semantic_schemas_stay_synchronized() -> None:
    package_root = Path(__file__).resolve().parents[3]
    protocol_root = package_root.parents[1]
    protocol_schema_dir = protocol_root / "schemas"
    if not protocol_schema_dir.exists():
        pytest.skip("protocol repository schemas are not available")

    for schema_file_name in (
        "semantic-search-packet.v1.schema.json",
        "semantic-query-packet.v1.schema.json",
        "semantic-read-packet.v1.schema.json",
        "semantic-provider-doctor.v1.schema.json",
        "semantic-language-registry.v1.schema.json",
        "semantic-language-registry.v1.schema.json",
        "provider-query-pack-descriptor.v1.schema.json",
        "semantic-source-location.v1.schema.json",
        "semantic-tree-sitter-provenance.v1.schema.json",
        "semantic-tree-sitter-query.v1.schema.json",
        "semantic-tree-sitter-grammar-profile.v1.schema.json",
        "semantic-graph.v1.schema.json",
        "semantic-type-surface.v1.schema.json",
        "semantic-dev-command-log.v1.schema.json",
    ):
        package_schema = json.loads(
            (package_root / "schemas" / schema_file_name).read_text(encoding="utf-8")
        )
        protocol_schema = json.loads(
            (protocol_schema_dir / schema_file_name).read_text(encoding="utf-8")
        )

        assert package_schema == protocol_schema
