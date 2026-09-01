from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from asp_python._semantic_search_graph_render import (
    compact_graph_seed_packet_text,
)


def _render_fields(fields: dict[str, Any]) -> str:
    return " ".join(f"{key}={value}" for key, value in fields.items())


def test_compact_graph_profiles_filter_to_rendered_aliases() -> None:
    workspace_renderer = (
        Path(os.environ["SEMANTIC_AGENT_PROTOCOL_BIN"])
        if os.environ.get("SEMANTIC_AGENT_PROTOCOL_BIN")
        else Path(__file__).resolve().parents[5] / ".bin" / "asp"
    )
    if not workspace_renderer.exists():
        pytest.skip("workspace graph renderer is not built")
    os.environ["SEMANTIC_AGENT_PROTOCOL_BIN"] = str(workspace_renderer)

    packet: dict[str, Any] = {
        "schemaId": "agent.semantic-protocols.semantic-search-packet",
        "schemaVersion": "1",
        "protocolId": "agent.semantic-protocols.search",
        "protocolVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "binary": "asp-python",
        "namespace": "agent.semantic-protocols.languages.python.asp-python",
        "method": "search/owner",
        "projectRoot": ".",
        "view": "seeds",
        "renderMode": "compact",
        "header": {"kind": "search-owner", "fields": {}},
        "nodes": [],
        "edges": [],
        "nextActions": [
            {"kind": "owner", "target": "src/pkg/service.py"},
            {"kind": "tests", "target": "tests/test_service.py"},
        ],
        "owners": [],
        "hits": [],
        "findings": [],
        "notes": [],
        "searchSynthesis": {"algorithm": "seed-frontier"},
        "reasoningProfiles": [
            {
                "profile": "owner-query",
                "selectors": [
                    {"kind": "owner", "alias": "O", "required": True},
                    {"kind": "query", "alias": "Q", "required": True},
                ],
                "returns": ["items", "tests", "dependency-usage"],
            },
            {
                "profile": "query-deps",
                "selectors": [
                    {"kind": "query", "alias": "Q", "required": True},
                    {"kind": "dependency", "alias": "D", "required": True},
                ],
                "returns": ["owners", "imports", "usage-tests"],
            },
            {
                "profile": "owner-tests",
                "selectors": [
                    {"kind": "owner", "alias": "O", "required": True},
                ],
                "returns": [
                    "covering-tests",
                    "test-entrypoints",
                    "fixtures",
                ],
            },
            {
                "profile": "finding-frontier",
                "selectors": [
                    {"kind": "finding", "alias": "F", "required": True},
                    {"kind": "owner", "alias": "O", "required": False},
                ],
                "returns": ["affected-owners", "tests", "verification-actions"],
            },
        ],
    }

    output = compact_graph_seed_packet_text(packet, _render_fields)

    assert "aliases: graph:{G=search,O=owner,T=test}" in output
    assert "entries=owner-tests(O=>covering-tests+test-entrypoints+fixtures)" in output
    assert "owner-query(" not in output
    assert "query-deps(" not in output
    assert "finding-frontier(" not in output
