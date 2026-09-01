from __future__ import annotations

import io
import json
from pathlib import Path

from asp_python import run_cli


def test_cli_query_registry_owns_structural_selector_projection(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "doctor", "--json", str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    descriptors = payload["registry"]["languages"][0]["methodDescriptors"]
    query = next(
        descriptor for descriptor in descriptors if descriptor["method"] == "query"
    )
    assert query["outputModes"] == ["frontier", "json"]
    assert "codeOutput" not in query
    assert any(
        descriptor["method"] == "query/exact-selector-native-v1"
        for descriptor in descriptors
    )
    assert all(
        "owner-local-projection" not in descriptor["method"]
        for descriptor in descriptors
    )


def test_cli_query_rejects_removed_from_hook_option(tmp_path: Path) -> None:
    stderr = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--workspace",
            str(tmp_path),
        ],
        stdout=io.StringIO(),
        stderr=stderr,
        cwd=tmp_path,
    )

    assert exit_code == 2
    assert "unknown query option: --from-hook" in stderr.getvalue()
