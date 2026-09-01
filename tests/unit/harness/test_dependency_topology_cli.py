from __future__ import annotations

import io
import json
import re
from pathlib import Path

from asp_python._cli_args import ProtocolArgs
from asp_python._cli_protocol import run_protocol_cli


def test_dependency_topology_cli_emits_canonical_packet(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "requests>=2.31\n",
        encoding="utf-8",
    )
    args = ProtocolArgs.parse(
        [
            "search",
            "dependency-topology",
            "--json",
            "--workspace",
            str(tmp_path),
        ]
    )
    assert args is not None
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_protocol_cli(
        args,
        stdout=stdout,
        stderr=stderr,
        stdin="",
        cwd=tmp_path,
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    packet = json.loads(stdout.getvalue())
    assert packet["packetKind"] == "dependency-topology"
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", packet["fingerprint"])
    assert packet["graph"]["nodes"] == [
        {
            "id": "dependency:requests",
            "kind": "dependency",
            "value": "requests",
            "path": "requirements.txt",
            "fields": {
                "dependencyName": "requests",
                "manifestPath": "requirements.txt",
            },
        },
        {
            "id": "dependency-version:requests",
            "kind": "dependency-version",
            "value": ">=2.31",
            "fields": {"version": ">=2.31"},
        },
    ]
    assert packet["graph"]["edges"] == [
        {
            "source": "dependency:requests",
            "target": "dependency-version:requests",
            "relation": "version_locked",
        }
    ]
