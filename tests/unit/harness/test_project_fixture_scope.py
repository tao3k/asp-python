from __future__ import annotations

from pathlib import Path

from asp_python import run_asp_python


def test_run_asp_python_skips_test_fixture_sources_by_default(
    tmp_path: Path,
) -> None:
    """Keep borrowed fixture projects out of root policy scans."""

    src = tmp_path / "src"
    fixture_src = tmp_path / "tests" / "fixtures" / "parser-compact" / "project" / "src"
    src.mkdir()
    fixture_src.mkdir(parents=True)
    source_file = src / "library.py"
    fixture_file = fixture_src / "borrowed_library.py"
    source_file.write_text('"""Library docs."""\n\nVALUE = 1\n', encoding="utf-8")
    fixture_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert report.is_clean
    assert [module.path for module in report.modules] == [str(source_file)]
