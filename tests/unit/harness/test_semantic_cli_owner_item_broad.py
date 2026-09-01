from __future__ import annotations

import io
from pathlib import Path

from asp_python._cli import run_cli


def _write_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'sample'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "service.py").write_text(
        "\n".join(
            [
                "def item_query_payload():",
                "    return None",
                "def candidate_route():",
                "    return None",
                "def fallback_mode():",
                "    return None",
                "def owner_top_items():",
                "    return None",
            ]
        ),
        encoding="utf-8",
    )


def test_owner_item_broad_fallback_uses_names_only(tmp_path: Path) -> None:
    _write_project(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "item_query|candidate|fallback|owner_top",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )
    rendered = stdout.getvalue()

    assert exit_code == 0
    assert "match=fallback-contains" in rendered
    assert "output=names" in rendered
    assert "next=select-item" in rendered
    assert "|item item_query_payload kind=function" in rendered
    assert "|code path=src/pkg/service.py" not in rendered


def test_owner_item_miss_fallback_does_not_dump_code(tmp_path: Path) -> None:
    _write_project(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--query",
            "render_semantic_query_json|projection_from_code_line",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )
    rendered = stdout.getvalue()

    assert exit_code == 0
    assert "status=miss" in rendered
    assert "output=names" in rendered
    assert "next=revise-query" in rendered
    assert "|item item_query_payload kind=function" in rendered
    assert "|code path=src/pkg/service.py" not in rendered
