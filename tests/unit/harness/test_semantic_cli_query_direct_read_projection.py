from __future__ import annotations

import io
from pathlib import Path

from pytest import CaptureFixture

from python_lang_project_harness._cli import run_cli


def test_query_from_hook_line_range_code_rejects_source_locator_hint(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'sample'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "sample.py").write_text(
        "\n".join(
            [
                "def first():",
                "    return 'first'",
                "",
                "def second():",
                "    return 'second'",
            ]
        ),
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--selector",
            "src/sample.py:1-5",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
        cwd=tmp_path,
    )

    assert exit_code == 3
    assert stdout.getvalue() == ""
    assert "status=selector-not-materialized" in capsys.readouterr().err
