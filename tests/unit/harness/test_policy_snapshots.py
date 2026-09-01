from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from snapshot_support import assert_snapshot, normalize_temp_root

from asp_python import (
    render_python_lang_harness,
    run_asp_python,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_py_mod_r001_wildcard_import_snapshot(tmp_path: Path) -> None:
    source = _src(tmp_path) / "module.py"
    source.write_text('"""Module docs."""\n\nfrom tools import *\n', encoding="utf-8")

    _assert_project_snapshot(tmp_path, "PY-MOD-R001", "py_mod_r001_wildcard_import")


def test_python_syntax_invalid_snapshot(tmp_path: Path) -> None:
    source = _src(tmp_path) / "broken.py"
    source.write_text("def broken(:\n    pass\n", encoding="utf-8")

    _assert_project_snapshot(
        tmp_path,
        "python.syntax.invalid",
        "python_syntax_invalid",
    )


def test_python_compile_invalid_snapshot(tmp_path: Path) -> None:
    source = _src(tmp_path) / "bad_scope.py"
    source.write_text("return 1\n", encoding="utf-8")

    _assert_project_snapshot(
        tmp_path,
        "python.compile.invalid",
        "python_compile_invalid",
    )


def test_py_mod_r002_bare_print_snapshot(tmp_path: Path) -> None:
    source = _src(tmp_path) / "module.py"
    source.write_text(
        '"""Module docs."""\n\n\ndef run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )

    _assert_project_snapshot(tmp_path, "PY-MOD-R002", "py_mod_r002_bare_print")


def test_py_mod_r003_facade_all_snapshot(tmp_path: Path) -> None:
    package = _src(tmp_path) / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("from .api import Runner\n", encoding="utf-8")
    (package / "api.py").write_text("class Runner:\n    pass\n", encoding="utf-8")

    _assert_project_snapshot(tmp_path, "PY-MOD-R003", "py_mod_r003_facade_all")


def test_py_mod_r004_breakpoint_snapshot(tmp_path: Path) -> None:
    source = _src(tmp_path) / "module.py"
    source.write_text(
        '"""Module docs."""\n\n\ndef run() -> None:\n    breakpoint()\n',
        encoding="utf-8",
    )

    _assert_project_snapshot(tmp_path, "PY-MOD-R004", "py_mod_r004_breakpoint")


def test_py_mod_r006_module_bloat_snapshot(tmp_path: Path) -> None:
    source = _src(tmp_path) / "feature.py"
    source.write_text(_large_multi_responsibility_module_source(), encoding="utf-8")

    _assert_project_snapshot(tmp_path, "PY-MOD-R006", "py_mod_r006_module_bloat")


def test_py_mod_r007_reasoning_tree_shadow_snapshot(tmp_path: Path) -> None:
    package = _src(tmp_path) / "pkg"
    shadow_package = package / "domain"
    shadow_package.mkdir(parents=True)
    (package / "domain.py").write_text(
        '"""Domain module owner."""\n',
        encoding="utf-8",
    )
    (shadow_package / "__init__.py").write_text(
        '"""Domain package owner."""\n',
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-MOD-R007",
        "py_mod_r007_reasoning_tree_shadow",
    )


def test_py_proj_r001_src_layout_snapshot(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text('"""Package docs."""\n', encoding="utf-8")
    (package / "py.typed").write_text("", encoding="utf-8")
    _write_pyproject(tmp_path, packages='["pkg"]')

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-001", "py_proj_r001_src_layout"
    )


def test_py_proj_r002_declared_package_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    _write_pyproject(tmp_path, packages='["src/missing_pkg"]')

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-002", "py_proj_r002_declared_package"
    )


def test_py_proj_r003_py_typed_snapshot(tmp_path: Path) -> None:
    package = _src(tmp_path) / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        '"""Package docs."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    _write_pyproject(tmp_path, packages='["src/pkg"]')

    _assert_project_snapshot(tmp_path, "PY-AGENT-PROJECT-003", "py_proj_r003_py_typed")


def test_py_proj_r004_typed_annotations_snapshot(tmp_path: Path) -> None:
    package = _src(tmp_path) / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text('"""Package docs."""\n', encoding="utf-8")
    (package / "py.typed").write_text("", encoding="utf-8")
    (package / "service.py").write_text(
        '"""Service helpers."""\n\n\ndef build(value):\n    return value\n',
        encoding="utf-8",
    )
    _write_pyproject(tmp_path, packages='["src/pkg"]')

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-004", "py_proj_r004_typed_annotations"
    )


def test_py_proj_r005_project_name_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
requires-python = ">=3.12"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-005", "py_proj_r005_project_name"
    )


def test_py_proj_r006_requires_python_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snapshot-package"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-006", "py_proj_r006_requires_python"
    )


def test_py_proj_r007_build_requires_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snapshot-package"
requires-python = ">=3.12"

[build-system]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-007", "py_proj_r007_build_requires"
    )


def test_py_proj_r008_import_names_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snapshot-package"
requires-python = ">=3.12"
import-names = ["missing_pkg"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-008", "py_proj_r008_import_names"
    )


def test_py_proj_r009_entry_point_target_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snapshot-package"
requires-python = ">=3.12"

[project.scripts]
snapshot-cli = "missing_pkg.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-PROJECT-009",
        "py_proj_r009_entry_point_target",
    )


def test_py_proj_r010_pytest_gate_snapshot(tmp_path: Path) -> None:
    _src(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snapshot-package"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path, "PY-AGENT-PROJECT-010", "py_proj_r010_pytest_gate"
    )


def test_py_proj_r011_verification_profile_snapshot(tmp_path: Path) -> None:
    package = _src(tmp_path) / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        '"""Package docs."""\nfrom .api import build\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text(
        '"""API docs."""\n\n\ndef build() -> str:\n    return "ok"\n',
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snapshot-package"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--python-project-harness"]
""".lstrip(),
        encoding="utf-8",
    )

    _assert_project_snapshot(
        tmp_path,
        "PY-AGENT-PROJECT-011",
        "py_proj_r011_verification_profile",
    )


def test_py_test_r001_root_pytest_snapshot(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_scattered.py").write_text(
        "def test_value() -> None:\n    assert True\n", encoding="utf-8"
    )

    _assert_project_snapshot(tmp_path, "PY-TEST-R001", "py_test_r001_root_pytest")


def test_py_test_r002_unexpected_root_snapshot(tmp_path: Path) -> None:
    (tmp_path / "tests" / "misc").mkdir(parents=True)

    _assert_project_snapshot(tmp_path, "PY-TEST-R002", "py_test_r002_unexpected_root")


def test_py_test_r003_unit_bloat_snapshot(tmp_path: Path) -> None:
    unit = tmp_path / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "test_large_policy.py").write_text(
        _large_unit_test_source(), encoding="utf-8"
    )

    _assert_project_snapshot(tmp_path, "PY-TEST-R003", "py_test_r003_unit_bloat")


def _assert_project_snapshot(root: Path, rule_id: str, snapshot_name: str) -> None:
    report = run_asp_python(root)
    findings = tuple(
        finding for finding in report.findings if finding.rule_id == rule_id
    )
    filtered = replace(report, findings=findings)
    assert len(filtered.findings) == 1, (
        f"expected one {rule_id} finding, got {filtered.findings!r}"
    )
    rendered = normalize_temp_root(render_python_lang_harness(filtered), root)
    assert_snapshot(
        f"unit_test__policy_snapshot__{snapshot_name}",
        rendered,
        source="tests/unit/harness/test_policy_snapshots.py",
    )


def _src(root: Path) -> Path:
    path = root / "src"
    path.mkdir(exist_ok=True)
    return path


def _write_pyproject(root: Path, *, packages: str) -> None:
    (root / "pyproject.toml").write_text(
        f"""
[project]
name = "snapshot-package"
requires-python = ">=3.12"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = {packages}
""".lstrip(),
        encoding="utf-8",
    )


def _large_multi_responsibility_module_source() -> str:
    blocks = ['"""Large feature module."""\n']
    for index in range(20):
        blocks.append(
            f"""
class Service{index}:
    def __init__(self, value: int) -> None:
        self.value = value

    def read(self) -> int:
        return self.value

    def write(self, value: int) -> None:
        self.value = value

    def render(self) -> str:
        return str(self.value)


def build_{index}(value: int) -> Service{index}:
    return Service{index}(value)


def parse_{index}(value: str) -> int:
    return int(value)
"""
        )
    return "\n".join(blocks)


def _large_unit_test_source() -> str:
    parts: list[str] = []
    for index in range(10):
        parts.append(
            f"""
def test_large_{index}() -> None:
    value = {index}
    assert value == {index}
"""
        )
        for helper_index in range(30):
            parts.append(f"    assert value + {helper_index} >= {index}\n")
    return "\n".join(parts)
