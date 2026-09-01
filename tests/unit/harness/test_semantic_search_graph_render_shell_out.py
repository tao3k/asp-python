from __future__ import annotations

import json
from pathlib import Path

import pytest

from asp_python._semantic_search_graph_render import (
    SEMANTIC_AGENT_PROTOCOL_BIN_ENV,
    CompactGraphRenderError,
    compact_graph_seed_packet_text,
    render_compact_graph_packet,
)


def test_compact_graph_renderer_shells_out_to_protocol_bin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    argv_path = tmp_path / "argv.txt"
    stdin_path = tmp_path / "stdin.json"
    protocol_bin = tmp_path / "semantic-agent-protocol"
    protocol_bin.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$@" > "$ASP_ARGV_PATH"\n'
        'cat > "$ASP_STDIN_PATH"\n'
        'printf "[search-lexical] q=test\\n"\n'
    )
    protocol_bin.chmod(0o755)
    monkeypatch.setenv(SEMANTIC_AGENT_PROTOCOL_BIN_ENV, str(protocol_bin))
    monkeypatch.setenv("ASP_ARGV_PATH", str(argv_path))
    monkeypatch.setenv("ASP_STDIN_PATH", str(stdin_path))

    packet = {"header": {"kind": "search-lexical"}}

    output = render_compact_graph_packet(packet, seed_limit=3)

    assert output == "[search-lexical] q=test\n"
    assert argv_path.read_text().splitlines() == [
        "graph",
        "render",
        "--packet",
        "-",
        "--view",
        "seeds",
        "--seeds",
        "3",
    ]
    assert json.loads(stdin_path.read_text()) == packet


def test_compact_graph_renderer_missing_bin_does_not_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        SEMANTIC_AGENT_PROTOCOL_BIN_ENV,
        str(tmp_path / "missing-semantic-agent-protocol"),
    )

    with pytest.raises(CompactGraphRenderError, match="not found"):
        render_compact_graph_packet({"header": {"kind": "search-lexical"}})


def test_compact_graph_seed_packet_appends_non_graph_flow_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdin_path = tmp_path / "stdin.json"
    protocol_bin = tmp_path / "semantic-agent-protocol"
    protocol_bin.write_text(
        "#!/bin/sh\n"
        'cat > "$ASP_STDIN_PATH"\n'
        'printf "[search-ingest] root=. alg=seed-frontier\\n"\n'
        'printf "G>{}\\n"\n'
        'printf "rank= frontier=\\n"\n',
        encoding="utf-8",
    )
    protocol_bin.chmod(0o755)
    monkeypatch.setenv(SEMANTIC_AGENT_PROTOCOL_BIN_ENV, str(protocol_bin))
    monkeypatch.setenv("ASP_STDIN_PATH", str(stdin_path))

    packet = {
        "header": {"kind": "search-ingest"},
        "notes": [
            {
                "kind": "stdin-required",
                "message": "search ingest consumes stdin candidate paths",
            }
        ],
        "nextActions": [
            {"kind": "owner", "target": "src/service.py"},
            {
                "kind": "prime",
                "target": "search prime --view seeds",
                "scope": "project-discovery",
            },
        ],
    }

    output = compact_graph_seed_packet_text(packet, lambda _fields: "")

    rendered_packet = json.loads(stdin_path.read_text())
    assert rendered_packet["nextActions"] == [
        {"kind": "owner", "target": "src/service.py"}
    ]
    assert "|note kind=stdin-required" in output
    assert "|next prime:" in output
    assert "owner:path(search prime" not in output
