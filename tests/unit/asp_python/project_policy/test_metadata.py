from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python._project_metadata import (
    read_python_project_metadata,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_read_python_project_metadata_collects_hatch_package_roots(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    _write_pyproject(
        tmp_path,
        packages='["src/example_pkg"]',
        project_name="example-pkg",
        requires_python=">=3.12",
        build_backend="hatchling.build",
    )

    metadata = read_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.has_project_table is True
    assert metadata.has_build_system_table is True
    assert metadata.project_name == "example-pkg"
    assert metadata.requires_python == ">=3.12"
    assert metadata.build_backend == "hatchling.build"
    assert metadata.build_requires == ("hatchling",)
    assert metadata.wheel_packages == ("src/example_pkg",)
    assert metadata.package_roots == (package,)
    assert metadata.import_names == ()


def test_read_python_project_metadata_returns_none_without_pyproject(
    tmp_path: Path,
) -> None:
    assert read_python_project_metadata(tmp_path) is None


def test_read_python_project_metadata_returns_none_for_malformed_pyproject(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text("[project\n", encoding="utf-8")

    assert read_python_project_metadata(tmp_path) is None


def test_read_python_project_metadata_ignores_unsupported_package_values(
    tmp_path: Path,
) -> None:
    _write_pyproject(tmp_path, packages="[42]")

    metadata = read_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.wheel_packages == ()
    assert metadata.package_roots == ()


def test_read_python_project_metadata_keeps_tool_only_pyproject_non_package(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
""".lstrip(),
        encoding="utf-8",
    )

    metadata = read_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.has_project_table is False
    assert metadata.has_build_system_table is False
    assert metadata.project_name is None
    assert metadata.requires_python is None
    assert metadata.build_backend is None
    assert metadata.build_requires == ()


def test_read_python_project_metadata_compacts_duplicate_package_roots(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    _write_pyproject(
        tmp_path,
        packages='["src/example_pkg", "src/./example_pkg", 42, "src/example_pkg"]',
    )

    metadata = read_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.wheel_packages == ("src/example_pkg",)
    assert metadata.package_roots == (package,)


def _write_pyproject(
    project_root: Path,
    *,
    packages: str,
    project_name: str = "example-pkg",
    requires_python: str = ">=3.12",
    build_backend: str = "hatchling.build",
) -> None:
    (project_root / "pyproject.toml").write_text(
        f"""
[project]
name = "{project_name}"
requires-python = "{requires_python}"

[build-system]
requires = ["hatchling"]
build-backend = "{build_backend}"

[tool.hatch.build.targets.wheel]
packages = {packages}
""".lstrip(),
        encoding="utf-8",
    )
