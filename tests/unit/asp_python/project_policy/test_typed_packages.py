from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import run_asp_python

if TYPE_CHECKING:
    from pathlib import Path


def test_project_policy_blocks_missing_py_typed_for_public_package(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-003", str(package)),
    ]


def test_project_policy_blocks_missing_py_typed_for_public_facade_imports(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\nfrom .service import Service\n\n__all__ = ("Service",)\n',
        encoding="utf-8",
    )
    (package / "service.py").write_text(
        '"""Service implementation."""\n\n\nclass Service:\n    pass\n',
        encoding="utf-8",
    )
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-003", str(package)),
    ]


def test_project_policy_allows_private_package_without_py_typed(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Internal package."""\n', encoding="utf-8")
    (package / "_internal.py").write_text(
        '"""Internal helpers."""\n\n\ndef _build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert report.is_clean


def test_project_policy_accepts_src_package_with_py_typed(tmp_path: Path) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert report.is_clean


def test_project_policy_accepts_nested_src_package_with_py_typed(
    tmp_path: Path,
) -> None:
    package = tmp_path / "packages" / "python" / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["packages/python/src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert report.is_clean


def test_project_policy_blocks_unannotated_public_callable_in_typed_package(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n', encoding="utf-8"
    )
    (package / "service.py").write_text(
        '"""Service helpers."""\n\n\ndef build(value):\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-004", str(package / "service.py")),
    ]
    assert "PY-AGENT-POLICY-002" not in {finding.rule_id for finding in report.findings}


def test_project_policy_blocks_unannotated_public_method_in_typed_package(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n', encoding="utf-8"
    )
    (package / "service.py").write_text(
        '"""Service helpers."""\n\n\nclass Service:\n    def build(self, value):\n        return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-004", str(package / "service.py")),
    ]
    assert report.findings[0].source_line == "    def build(self, value):"


def test_project_policy_allows_private_callable_without_annotations_in_typed_package(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n', encoding="utf-8"
    )
    (package / "service.py").write_text(
        '"""Service helpers."""\n\n\ndef _build(value):\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert report.is_clean


def test_project_policy_accepts_annotated_method_in_typed_package(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package public API."""\n', encoding="utf-8"
    )
    (package / "service.py").write_text(
        '"""Service helpers."""\n\n\nclass Service:\n    def build(self, value: int) -> int:\n        return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["src/example_pkg"]')

    report = run_asp_python(tmp_path)

    assert report.is_clean


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
