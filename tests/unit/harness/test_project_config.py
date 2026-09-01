from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import read_asp_python_config
from python_lang_parser import PythonDiagnosticSeverity

if TYPE_CHECKING:
    from pathlib import Path


def test_read_asp_python_config_from_pyproject(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.asp-python]
include_tests = false
source_dir_names = ["lib"]
test_dir_names = ["checks"]
extra_path_names = ["tools", "tools"]
ignored_dir_names = ["__pycache__", "generated"]
disabled_rule_ids = ["PY-MOD-R002", "PY-MOD-R002"]
blocking_rule_ids = ["PY-AGENT-POLICY-007"]
blocking_severities = ["error"]
""".lstrip(),
        encoding="utf-8",
    )

    config = read_asp_python_config(tmp_path)

    assert config is not None
    assert config.include_tests is False
    assert config.source_dir_names == ("lib",)
    assert config.test_dir_names == ("checks",)
    assert config.extra_path_names == ("tools",)
    assert config.ignored_dir_names == frozenset({"__pycache__", "generated"})
    assert config.disabled_rule_ids == frozenset({"PY-MOD-R002"})
    assert config.blocking_rule_ids == frozenset({"PY-AGENT-POLICY-007"})
    assert config.blocking_severities == frozenset({PythonDiagnosticSeverity.ERROR})


def test_read_asp_python_config_returns_none_without_table(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
""".lstrip(),
        encoding="utf-8",
    )

    assert read_asp_python_config(tmp_path) is None


def test_read_asp_python_config_rejects_invalid_values(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.asp-python]
blocking_severities = ["critical"]
""".lstrip(),
        encoding="utf-8",
    )

    try:
        read_asp_python_config(tmp_path)
    except ValueError as error:
        assert "unknown severity: critical" in str(error)
    else:
        raise AssertionError("invalid project harness config should fail")
