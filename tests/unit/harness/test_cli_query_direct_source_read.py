import io
from pathlib import Path

from python_lang_project_harness._cli import run_cli


def test_cli_query_direct_source_read_code_rejects_source_locator_hint(
    tmp_path: Path,
) -> None:
    source = tmp_path / "tests" / "unit" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "def target(value: int) -> int:\n    return value + 1\n", encoding="utf-8"
    )
    stderr = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--selector",
            "tests/unit/example.py:1-2",
            "--workspace",
            str(tmp_path),
            "--code",
        ],
        stdout=io.StringIO(),
        stderr=stderr,
        cwd=tmp_path,
    )

    assert exit_code == 3
    assert "status=selector-not-materialized" in stderr.getvalue()
    assert "nextAction=refresh-parser-projection" in stderr.getvalue()


def test_cli_query_direct_source_read_code_rejects_missing_structural_selector(
    tmp_path: Path,
) -> None:
    source = tmp_path / "tests" / "unit" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("def target() -> None:\n    pass\n", encoding="utf-8")
    stderr = io.StringIO()

    exit_code = run_cli(
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--selector",
            "tests/unit/example.py",
            "--workspace",
            str(tmp_path),
            "--code",
        ],
        stdout=io.StringIO(),
        stderr=stderr,
        cwd=tmp_path,
    )

    assert exit_code == 3
    assert "status=selector-not-materialized" in stderr.getvalue()


def test_cli_query_code_rejects_trailing_project_root(tmp_path: Path) -> None:
    source = tmp_path / "tests" / "unit" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("def target() -> None:\n    pass\n", encoding="utf-8")

    cases = (
        [
            "query",
            "--from-hook",
            "owner-local-projection",
            "--selector",
            "tests/unit/example.py:1-2",
            "--code",
            str(tmp_path),
        ],
        [
            "query",
            "tests/unit/example.py",
            "--term",
            "target",
            "--code",
            str(tmp_path),
        ],
        [
            "query",
            "--treesitter-query",
            "(function_definition name: (identifier) @function.name)",
            "--selector",
            "tests/unit/example.py:1-2",
            "--code",
            str(tmp_path),
        ],
        [
            "search",
            "owner",
            "tests/unit/example.py",
            "items",
            "--query",
            "target",
            "--code",
            str(tmp_path),
        ],
    )

    for args in cases:
        stderr = io.StringIO()

        exit_code = run_cli(args, stdout=io.StringIO(), stderr=stderr, cwd=tmp_path)

        assert exit_code == 2
        assert "does not accept positional WORKSPACE" in stderr.getvalue()
