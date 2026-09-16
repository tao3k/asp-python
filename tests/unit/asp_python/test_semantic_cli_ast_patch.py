from __future__ import annotations

import io
import json
from pathlib import Path

from asp_python import run_cli


def test_ast_patch_dry_run_returns_provider_unsupported_operation_receipt(
    tmp_path: Path,
) -> None:
    packet = {
        "target": {
            "ownerPath": "src/example.py",
            "locator": "src/example.py#fn:example",
            "read": "src/example.py:1:4",
        },
        "operation": {"op": "remove_statement"},
    }
    stdout = io.StringIO()

    exit_code = run_cli(
        ["ast-patch", "dry-run", "--packet", "-", str(tmp_path)],
        stdout=stdout,
        stdin=json.dumps(packet),
    )
    receipt = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert receipt["status"] == "failed"
    assert receipt["capability"] == "provider-ast-dry-run"
    assert receipt["failureKind"] == "unsupported-operation"
    assert receipt["supportedOperations"] == []
    assert receipt["operation"] == "remove_statement"
    assert receipt["target"]["read"] == "src/example.py:1:4"
