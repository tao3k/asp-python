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

    for package_schema_path in sorted((package_root / "schemas").glob("*.schema.json")):
        protocol_schema_path = protocol_schema_dir / package_schema_path.name
        if not protocol_schema_path.exists():
            continue
        package_schema = json.loads(package_schema_path.read_text(encoding="utf-8"))
        protocol_schema = json.loads(protocol_schema_path.read_text(encoding="utf-8"))

        assert package_schema == protocol_schema
