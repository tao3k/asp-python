import io
from pathlib import Path

from python_lang_project_harness._cli import run_cli


def test_query_from_hook_line_range_code_rejects_source_locator_hint(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "src" / "package" / "module.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        "def selected():\n    return 'direct'\n",
        encoding="utf-8",
    )
    stderr = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--selector",
            "src/package/module.py:1-2",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=io.StringIO(),
        stderr=stderr,
        cwd=tmp_path,
    )

    assert exit_code == 3
    assert "status=selector-not-materialized" in stderr.getvalue()


def test_query_file_selector_code_requires_parser_owned_identity(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "tests" / "test_docs_rfc_skill_contracts.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        "def test_skill_mentions_hook_install():\n    assert 'asp hook install'\n",
        encoding="utf-8",
    )
    stderr = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--selector",
            "tests/test_docs_rfc_skill_contracts.py",
            "--term",
            "hook",
            "--code",
            "--workspace",
            str(tmp_path),
        ],
        stdout=io.StringIO(),
        stderr=stderr,
        cwd=tmp_path,
    )

    assert exit_code == 3
    assert "status=selector-not-materialized" in stderr.getvalue()
