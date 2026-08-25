from __future__ import annotations

import tomllib
from importlib import metadata
from pathlib import Path

import python_lang_parser
import python_lang_project_harness


def test_distribution_metadata_uses_project_name() -> None:
    project = metadata.metadata("python-lang-project-harness")

    assert project["Name"] == "python-lang-project-harness"
    assert project["Version"] == "0.1.0"


def test_runtime_package_identity_matches_distribution_metadata() -> None:
    installed_version = metadata.version("python-lang-project-harness")

    assert python_lang_project_harness.DISTRIBUTION_NAME == (
        "python-lang-project-harness"
    )
    assert python_lang_project_harness.__version__ == installed_version
    assert python_lang_parser.__version__ == installed_version


def test_distribution_import_packages_are_current_project_surfaces() -> None:
    top_level_names = {
        path.parts[0]
        for path in metadata.files("python-lang-project-harness") or ()
        if path.parts
        and not path.parts[0].endswith(".dist-info")
        and path.parts[0] != ".."
        and not path.parts[0].startswith("_editable")
    }

    assert top_level_names <= {
        "python_lang_parser",
        "python_lang_project_harness",
    }


def test_distribution_exposes_console_script() -> None:
    scripts = {
        entry_point.name: entry_point.value
        for entry_point in metadata.entry_points(group="console_scripts")
    }

    assert scripts["asp-python"] == ("python_lang_project_harness:run_cli_from_env")


def test_distribution_exposes_pytest_optional_dependency() -> None:
    project = metadata.metadata("python-lang-project-harness")

    assert "pytest" in project.get_all("Provides-Extra", [])
    assert any(
        dependency.startswith("pytest>=8.0;") and "extra == 'pytest'" in dependency
        for dependency in project.get_all("Requires-Dist", [])
    )


def test_distribution_exposes_pytest_plugin_entry_point() -> None:
    plugins = {
        entry_point.name: entry_point.value
        for entry_point in metadata.entry_points(group="pytest11")
    }

    assert plugins["python_lang_project_harness"] == (
        "python_lang_project_harness.pytest_plugin"
    )


def test_wheel_package_configuration_lists_current_import_packages() -> None:
    project_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "pyproject.toml").is_file()
    )
    pyproject = tomllib.loads(
        (project_root / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/python_lang_parser",
        "src/python_lang_project_harness",
    ]
    assert pyproject["project"]["import-names"] == [
        "python_lang_parser",
        "python_lang_project_harness",
    ]
