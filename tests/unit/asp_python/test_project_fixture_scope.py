from __future__ import annotations

from pathlib import Path

import pytest

from asp_python import run_asp_python
from asp_python._discovery import discover_python_files


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


def test_discovery_prunes_ignored_directories_before_descending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "src" / "library.py"

    def observed_walk(_root: Path):
        root_directories = [".venv", "src", "target"]
        yield tmp_path, root_directories, []
        assert root_directories == ["src"]
        yield tmp_path / "src", [], ["library.py"]

    monkeypatch.setattr(Path, "walk", observed_walk)

    assert discover_python_files([tmp_path]) == (source,)
