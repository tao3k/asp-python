from __future__ import annotations

import io
from pathlib import Path

from pytest import CaptureFixture

from python_lang_project_harness._cli import run_cli


def test_cli_query_direct_source_read_code_rejects_source_window(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        '\n[project]\nname = "demo-python"\nversion = "0.1.0"\nimport-names = ["pkg"]\n',
        encoding="utf-8",
    )
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "service.py").write_text(
        "def alpha(value: str) -> str:\n    return value.upper()\n",
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--selector",
            "src/pkg/service.py:1:2",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    assert exit_code == 3
    assert stdout.getvalue() == ""
    assert "status=selector-not-materialized" in capsys.readouterr().err
