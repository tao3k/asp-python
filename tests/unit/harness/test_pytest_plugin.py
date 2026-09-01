from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from asp_python._pytest_plugin_project import _package_scoped_root

if TYPE_CHECKING:
    from pathlib import Path


def test_pytest_plugin_collects_harness_item_from_dev_dependency(
    tmp_path: Path,
) -> None:
    _write_clean_project(tmp_path)

    result = _run_pytest_plugin(tmp_path, "--python-project-harness")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 passed" in result.stdout


def test_pytest_plugin_is_quiet_without_enable_option(
    tmp_path: Path,
) -> None:
    _write_clean_project(tmp_path)

    result = _run_pytest_plugin(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_pytest_plugin_can_be_enabled_from_pyproject_addopts(
    tmp_path: Path,
) -> None:
    _write_clean_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.pytest.ini_options]
addopts = ["--python-project-harness"]
""".lstrip(),
        encoding="utf-8",
    )

    result = _run_pytest_plugin(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 passed" in result.stdout


def test_pytest_plugin_runs_without_downstream_test_files(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")

    result = _run_pytest_plugin(tmp_path, "--python-project-harness")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_pytest_plugin_reports_compact_harness_failure(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    (tests / "test_placeholder.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    result = _run_pytest_plugin(tmp_path, "--python-project-harness")

    assert result.returncode == 1
    assert "rule=PY-MOD-R002 severity=warning" in result.stdout
    assert "|message Library module uses bare print" in result.stdout
    assert "src/library.py" in result.stdout
    assert str(tmp_path) not in result.stdout
    assert "../" not in result.stdout
    assert "FAILED python-project-harness" in result.stdout
    assert (
        "|repair replace bare print with a project-owned reporting surface"
        in result.stdout
    )


def test_pytest_plugin_scopes_package_target_to_nearest_project(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "packages" / "python" / "graphs"
    test_path = package_root / "tests" / "test_graphs.py"
    test_path.parent.mkdir(parents=True)
    (package_root / "pyproject.toml").write_text(
        """
[project]
name = "graphs"
version = "0.1.0"
""".lstrip(),
        encoding="utf-8",
    )
    test_path.write_text(
        "def test_graphs() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    assert (
        _package_scoped_root(
            tmp_path,
            ("packages/python/graphs/tests",),
            invocation_dir=tmp_path,
        )
        == package_root
    )


def test_pytest_plugin_keeps_workspace_scope_for_mixed_projects(
    tmp_path: Path,
) -> None:
    first = tmp_path / "packages" / "python" / "first"
    second = tmp_path / "packages" / "python" / "second"
    for package in (first, second):
        (package / "tests").mkdir(parents=True)
        (package / "pyproject.toml").write_text(
            '[project]\nname = "package"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        (package / "tests" / "test_package.py").write_text(
            "def test_package() -> None:\n    assert True\n",
            encoding="utf-8",
        )

    assert (
        _package_scoped_root(
            tmp_path,
            (
                "packages/python/first/tests",
                "packages/python/second/tests",
            ),
            invocation_dir=tmp_path,
        )
        is None
    )


def test_pytest_plugin_honors_dev_dependency_options(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    tests = tmp_path / "tests" / "unit"
    lib.mkdir()
    tests.mkdir(parents=True)
    (lib / "library.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    (tests / "test_bad.py").write_text(
        "def test_bad() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    (tests / "test_placeholder.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    result = _run_pytest_plugin(
        tmp_path,
        "--python-project-harness",
        "--python-project-harness-source-dir=lib",
        "--python-project-harness-no-tests",
        "--python-project-harness-error-only",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_pytest_plugin_honors_policy_rule_options(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    (tests / "test_placeholder.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    result = _run_pytest_plugin(
        tmp_path,
        "--python-project-harness",
        "--python-project-harness-disable-rule=PY-MOD-R002",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_pytest_plugin_loads_project_policy_config_from_pyproject(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.asp-python]
disabled_rule_ids = ["PY-MOD-R002"]
""".lstrip(),
        encoding="utf-8",
    )
    (src / "library.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    (tests / "test_placeholder.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    result = _run_pytest_plugin(tmp_path, "--python-project-harness")

    assert result.returncode == 0, result.stdout + result.stderr


def _write_clean_project(project_root: Path) -> None:
    src = project_root / "src"
    tests = project_root / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tests / "test_placeholder.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )


def _run_pytest_plugin(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *args],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
