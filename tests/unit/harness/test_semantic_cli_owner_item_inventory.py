"""Owner item inventory tests for the Python semantic CLI."""

from __future__ import annotations

import io
from pathlib import Path

from asp_python import run_cli


def test_cli_search_owner_items_without_query_returns_inventory(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "search",
            "owner",
            "src/pkg/service.py",
            "items",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert "[search-owner] q=src/pkg/service.py owner=1 item=" in rendered
    assert "|owner src/pkg/service.py " in rendered
    assert "|item SessionClient kind=class" in rendered
    assert " itemStatus=" not in rendered
    assert "|code " not in rendered
    assert "|hit " not in rendered
    assert "|synthesis " not in rendered
    assert "|next " not in rendered
    assert " next=syntax:SessionClient " in rendered
    assert " tsqRef=semantic-tree-sitter-query/python-owner-items.v1" in rendered


def _write_fixture(root: Path) -> None:
    (root / "pyproject.toml").write_text(
        '[project]\nname = "owner-item-inventory-fixture"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    package_dir = root / "src" / "pkg"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "service.py").write_text(
        "\n".join(
            [
                "class SessionClient:",
                "    def fetch_user(self, user_id: str) -> str:",
                "        return user_id",
                "",
                "def build_user(user_id: str) -> dict[str, str]:",
                "    return {'id': user_id}",
                "",
            ]
        ),
        encoding="utf-8",
    )
