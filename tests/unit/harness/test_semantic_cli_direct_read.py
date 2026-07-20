from __future__ import annotations

import io
from pathlib import Path

from python_lang_project_harness._cli import run_cli


def _write_demo_package(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        '\n[project]\nname = "demo-python"\nversion = "0.1.0"\nimport-names = ["pkg"]\n',
        encoding="utf-8",
    )
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "service.py").write_text(
        "\n".join(
            [
                "def alpha(value: str) -> str:",
                "    return value.upper()",
                "class Beta:",
                "    value: str",
            ]
        ),
        encoding="utf-8",
    )


def test_cli_query_plain_owner_path_still_uses_item_query(
    tmp_path: Path,
) -> None:
    _write_demo_package(tmp_path)
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--selector",
            "src/pkg/service.py",
            "--term",
            "alpha",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    assert "owner-local-projection" not in stdout.getvalue()
