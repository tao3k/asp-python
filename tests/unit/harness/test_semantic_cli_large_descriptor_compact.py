from __future__ import annotations

import io
import json
from pathlib import Path

from python_lang_project_harness._cli import run_cli


def test_cli_query_compacts_large_descriptor_return_lists(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo-python"
version = "0.1.0"
import-names = ["pkg"]
""".strip(),
        encoding="utf-8",
    )
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "catalog.py").write_text(
        "\n".join(
            [
                "from typing import Any",
                "",
                "def python_search_view_descriptors() -> list[dict[str, Any]]:",
                "    return [",
                "        _view('workspace', capabilities=[_semantic('workspace-router')]),",
                "        _view('prime', capabilities=[_semantic('package-prime-map')]),",
                "        _view('owner', requires_query=True, accepted_pipes=['items']),",
                "        _view('dependency', requires_query=True),",
                "        _view('deps', requires_query=True),",
                "        _view('api', requires_query=True),",
                "        _view('policy', requires_query=True),",
                "    ]",
            ]
        ),
        encoding="utf-8",
    )

    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "query",
            "--selector",
            "python://src/pkg/catalog.py#item/function/python_search_view_descriptors",
            "--term",
            "python_search_view_descriptors",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert exit_code == 0
    assert "return list[7] items=_view:workspace,_view:prime,_view:owner" in output
    assert "capabilities=[" not in output
    assert "truncated=true" not in output


def test_cli_query_compacts_large_descriptor_return_dict_shapes(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo-python"
version = "0.1.0"
import-names = ["pkg"]
""".strip(),
        encoding="utf-8",
    )
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "catalog.py").write_text(
        "\n".join(
            [
                "from typing import Any",
                "",
                "def python_view_descriptors() -> list[dict[str, Any]]:",
                "    return [",
                "        {'name': 'workspace', 'capabilities': ['workspace-router'], 'requires_query': False},",
                "        {'name': 'prime', 'capabilities': ['package-prime-map'], 'requires_query': False},",
                "        {'name': 'owner', 'accepted_pipes': ['items'], 'requires_query': True},",
                "        {'name': 'dependency', 'accepted_pipes': ['deps'], 'requires_query': True},",
                "        {'name': 'policy', 'accepted_pipes': ['tests'], 'requires_query': True},",
                "    ]",
                "",
                "def python_view_index() -> dict[str, dict[str, Any]]:",
                "    return {",
                "        'workspace': {'capabilities': ['workspace-router']},",
                "        'prime': {'capabilities': ['package-prime-map']},",
                "        'owner': {'accepted_pipes': ['items']},",
                "        'dependency': {'accepted_pipes': ['deps']},",
                "        'policy': {'accepted_pipes': ['tests']},",
                "    }",
            ]
        ),
        encoding="utf-8",
    )

    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "query",
            "--selector",
            "python://src/pkg/catalog.py#item/function/python_view_descriptors",
            "--term",
            "python_view_descriptors",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert exit_code == 0
    assert "return list[5] items=dict[3] name=workspace" in output
    assert "'capabilities':" not in output
    assert "truncated=true" not in output

    index_stdout = io.StringIO()
    index_exit_code = run_cli(
        [
            "query",
            "--selector",
            "python://src/pkg/catalog.py#item/function/python_view_index",
            "--term",
            "python_view_index",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=index_stdout,
    )
    index_output = index_stdout.getvalue()
    assert index_exit_code == 0
    assert "return dict[5] workspace=dict[1] prime=dict[1]" in index_output
    assert "'capabilities':" not in index_output
    assert "truncated=true" not in index_output

    json_stdout = io.StringIO()
    json_exit_code = run_cli(
        [
            "query",
            "--selector",
            "python://src/pkg/catalog.py#item/function/python_view_descriptors",
            "--term",
            "python_view_descriptors",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=json_stdout,
    )

    index_json_stdout = io.StringIO()
    index_json_exit_code = run_cli(
        [
            "query",
            "--selector",
            "python://src/pkg/catalog.py#item/function/python_view_index",
            "--term",
            "python_view_index",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=index_json_stdout,
    )

    packet = json.loads(json_stdout.getvalue())
    index_packet = json.loads(index_json_stdout.getvalue())
    code_by_name = {
        match["name"]: match["code"]
        for current_packet in (packet, index_packet)
        for match in current_packet["matches"]
    }
    assert json_exit_code == 0
    assert index_json_exit_code == 0
    assert (
        "return list[5] items=dict[3] name=workspace"
        in code_by_name["python_view_descriptors"]
    )
    assert (
        "return dict[5] workspace=dict[1] prime=dict[1]"
        in code_by_name["python_view_index"]
    )
    for current_packet in (packet, index_packet):
        for match in current_packet["matches"]:
            rendered = "\n".join(
                row["text"] for row in match["projection"]["renderedRows"]
            )
            assert rendered == match["code"]
