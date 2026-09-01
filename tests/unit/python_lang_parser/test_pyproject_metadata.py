from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_parser import parse_python_project_metadata

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_python_project_metadata_collects_modern_project_facts(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"
import-names = ["example_pkg", "_example_private ; private"]
import-namespaces = ["example_namespace"]
dependencies = ["httpx>=0.28"]

[project.optional-dependencies]
pytest = ["pytest>=8"]

[project.scripts]
example = "example_pkg.cli:main"

[project.entry-points.pytest11]
example_pkg = "example_pkg.pytest_plugin"

[dependency-groups]
docs = [
    { package = "mkdocs>=1.6" },
]
test = [
    "asp-python[pytest]>=0.1.0",
    { dependency = "ruff>=0.13" },
]

[tool.pytest.ini_options]
addopts = ["--import-mode=importlib", "--python-project-harness"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/example_pkg"]
""".lstrip(),
        encoding="utf-8",
    )

    metadata = parse_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.project_name == "example-pkg"
    assert metadata.requires_python == ">=3.12"
    assert metadata.build_backend == "hatchling.build"
    assert metadata.build_requires == ("hatchling",)
    assert [item.to_dict() for item in metadata.dependencies] == [
        {
            "requirement": "httpx>=0.28",
            "name": "httpx",
            "source": "project.dependencies",
            "group": None,
            "extra": None,
        },
        {
            "requirement": "pytest>=8",
            "name": "pytest",
            "source": "project.optional-dependencies",
            "group": None,
            "extra": "pytest",
        },
        {
            "requirement": "mkdocs>=1.6",
            "name": "mkdocs",
            "source": "dependency-groups",
            "group": "docs",
            "extra": None,
        },
        {
            "requirement": "asp-python[pytest]>=0.1.0",
            "name": "asp-python",
            "source": "dependency-groups",
            "group": "test",
            "extra": None,
        },
        {
            "requirement": "ruff>=0.13",
            "name": "ruff",
            "source": "dependency-groups",
            "group": "test",
            "extra": None,
        },
    ]
    assert metadata.pytest_options.addopts == (
        "--import-mode=importlib",
        "--python-project-harness",
    )
    assert metadata.pytest_options.enables_asp_python is True
    assert metadata.wheel_packages == ("src/example_pkg",)
    assert metadata.package_roots == (package,)
    assert [item.to_dict() for item in metadata.import_names] == [
        {
            "name": "example_pkg",
            "namespace": ["example_pkg"],
            "is_private": False,
            "source_value": "example_pkg",
        },
        {
            "name": "_example_private",
            "namespace": ["_example_private"],
            "is_private": True,
            "source_value": "_example_private ; private",
        },
    ]
    assert [item.to_dict() for item in metadata.import_namespaces] == [
        {
            "name": "example_namespace",
            "namespace": ["example_namespace"],
            "is_private": False,
            "source_value": "example_namespace",
        }
    ]
    assert [item.to_dict() for item in metadata.scripts] == [
        {
            "name": "example",
            "target": "example_pkg.cli:main",
            "kind": "console",
            "target_module": "example_pkg.cli",
            "target_namespace": ["example_pkg", "cli"],
            "target_object": ["main"],
        }
    ]
    assert [item.to_dict() for item in metadata.entry_points] == [
        {
            "group": "pytest11",
            "name": "example_pkg",
            "target": "example_pkg.pytest_plugin",
            "target_module": "example_pkg.pytest_plugin",
            "target_namespace": ["example_pkg", "pytest_plugin"],
            "target_object": [],
        }
    ]


def test_parse_python_project_metadata_strips_entry_point_extras(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[project.scripts]
example = "example_pkg.cli:main [rich]"
""".lstrip(),
        encoding="utf-8",
    )

    metadata = parse_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.scripts[0].target_module == "example_pkg.cli"
    assert metadata.scripts[0].target_namespace == ("example_pkg", "cli")
    assert metadata.scripts[0].target_object == ("main",)


def test_parse_python_project_metadata_derives_package_roots_from_import_names(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"
import-names = ["example_pkg"]
""".lstrip(),
        encoding="utf-8",
    )

    metadata = parse_python_project_metadata(tmp_path)

    assert metadata is not None
    assert metadata.wheel_packages == ()
    assert metadata.package_roots == (package,)
