from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_project_harness import run_python_project_harness

if TYPE_CHECKING:
    from pathlib import Path


def test_project_policy_noops_without_pyproject(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )

    report = run_python_project_harness(tmp_path)

    assert not any(
        finding.rule_id.startswith("PY-PROJ-") for finding in report.findings
    )


def test_project_policy_blocks_flat_layout_with_pyproject(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        '"""Package public API."""\n', encoding="utf-8"
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["pkg"]')

    report = run_python_project_harness(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-001", str(tmp_path / "pyproject.toml")),
    ]


def test_project_policy_accepts_pyproject_declared_nested_src_layout(
    tmp_path: Path,
) -> None:
    default_src = tmp_path / "src"
    package = tmp_path / "packages" / "python" / "src" / "tools"
    default_src.mkdir()
    package.mkdir(parents=True)
    (default_src / "ignored.py").write_text(
        "def broken(:\n    pass\n", encoding="utf-8"
    )
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["packages/python/src/tools"]')

    report = run_python_project_harness(tmp_path)

    assert report.is_clean
    assert report.project_resolution is not None
    assert report.project_resolution.source_paths == (package.parent,)


def test_project_policy_blocks_missing_declared_package_root(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    _write_pyproject(tmp_path, packages='["src/missing_pkg"]')

    report = run_python_project_harness(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-002", str(tmp_path / "pyproject.toml")),
    ]


def test_project_policy_blocks_package_root_without_init(tmp_path: Path) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_python_project_harness(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-002", str(package)),
    ]


def test_project_policy_deduplicates_declared_package_findings(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    _write_pyproject(
        tmp_path,
        packages='["src/missing_pkg", "src/./missing_pkg", "src/missing_pkg"]',
    )

    report = run_python_project_harness(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-002", str(tmp_path / "pyproject.toml")),
    ]


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
