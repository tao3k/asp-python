"""Public external type surface CLI tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from asp_python import run_cli


def test_cli_search_public_external_types_uses_public_api_facts(
    tmp_path: Path,
) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()
    json_stdout = io.StringIO()

    exit_code = run_cli(
        ["search", "public-external-types", "requests", "--workspace", str(tmp_path)],
        stdout=stdout,
    )
    json_exit_code = run_cli(
        [
            "search",
            "public-external-types",
            "requests",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=json_stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-public-external-types] q=requests")
    assert "package=requests" in rendered
    assert "|api path=src/pkg/service.py line=6" in rendered
    assert "reason=public-external-type" in rendered
    assert "confidence=direct" in rendered
    assert "|api path=src/pkg/service.py line=9" in rendered
    assert "reason=possible-public-external-type" in rendered
    assert "confidence=possible" in rendered

    packet = json.loads(json_stdout.getvalue())
    assert json_exit_code == 0
    assert packet["method"] == "search/public-external-types"
    assert packet["view"] == "public-external-types"
    assert packet["header"]["fields"]["package"] == "requests"
    type_surfaces = packet["typeSurfaces"]
    assert len(type_surfaces) == len(packet["hits"])
    assert any(
        surface["kind"] == "class"
        and surface["role"] == "external-dependency"
        and surface["package"] == "requests"
        and surface["carrier"]["name"] == "class SessionClient(requests.Session):"
        and surface["carrier"]["carrier"] == "class"
        and surface["carrier"]["external"] is True
        and surface["fields"]["confidence"] == "direct"
        for surface in type_surfaces
    )
    assert any(
        surface["kind"] == "function"
        and surface["carrier"]["name"] == "def fetch() -> Response:"
        and surface["fields"]["confidence"] == "possible"
        for surface in type_surfaces
    )
    assert any(
        hit["reason"] == "public-external-type"
        and hit["fields"]["dependency"] == "requests"
        and hit["fields"]["confidence"] == "direct"
        for hit in packet["hits"]
    )
    assert any(
        hit["reason"] == "possible-public-external-type"
        and hit["fields"]["dependency"] == "requests"
        and hit["fields"]["confidence"] == "possible"
        for hit in packet["hits"]
    )
