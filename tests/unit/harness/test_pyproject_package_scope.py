from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_project_harness import run_python_project_harness

if TYPE_CHECKING:
    from pathlib import Path


def test_run_python_project_harness_uses_pyproject_package_scope(
    tmp_path: Path,
) -> None:
    default_src = tmp_path / "src"
    package_source = tmp_path / "packages" / "python" / "src"
    package = package_source / "tools"
    tests = tmp_path / "tests" / "unit"
    default_src.mkdir()
    package.mkdir(parents=True)
    tests.mkdir(parents=True)
    (default_src / "ignored.py").write_text(
        "def broken(:\n    pass\n", encoding="utf-8"
    )
    source_file = package / "__init__.py"
    source_file.write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    test_file = tests / "test_tools.py"
    test_file.write_text(
        "def test_tools() -> None:\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["packages/python/src/tools"]
""".lstrip(),
        encoding="utf-8",
    )

    report = run_python_project_harness(tmp_path)

    assert report.is_clean
    assert [module.path for module in report.modules] == [
        str(source_file),
        str(test_file),
    ]
    assert report.project_resolution is not None
    assert report.project_resolution.source_paths == (package_source,)
    assert report.project_resolution.project_paths == (
        package_source,
        tmp_path / "tests",
    )
