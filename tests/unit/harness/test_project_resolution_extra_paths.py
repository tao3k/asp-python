from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_project_harness import run_python_project_harness

if TYPE_CHECKING:
    from pathlib import Path


def test_run_python_project_harness_can_include_extra_project_paths(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    examples = tmp_path / "examples"
    tool = tmp_path / "tools" / "check.py"
    shared = tmp_path.parent / "shared_tools"
    src.mkdir()
    examples.mkdir()
    tool.parent.mkdir()
    shared.mkdir()
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (examples / "demo.py").write_text('"""Demo docs."""\n', encoding="utf-8")
    tool.write_text('"""Tool docs."""\n', encoding="utf-8")
    (shared / "shared.py").write_text('"""Shared docs."""\n', encoding="utf-8")

    default_report = run_python_project_harness(tmp_path)
    report = run_python_project_harness(
        tmp_path,
        extra_path_names=("../shared_tools",),
    )

    assert [module.path for module in default_report.modules] == [
        str(examples / "demo.py"),
        str(src / "library.py"),
        str(tool),
    ]
    assert sorted(module.path for module in report.modules) == sorted(
        [
            str(examples / "demo.py"),
            str(shared / "shared.py"),
            str(src / "library.py"),
            str(tool),
        ]
    )
    assert report.project_resolution is not None
    assert report.project_resolution.extra_paths == (shared,)
    assert report.root_paths == (str(tmp_path), str(shared))
