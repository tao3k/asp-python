from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    AspPythonConfig,
    run_asp_python,
    run_python_lang_harness,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_project_runner_uses_configured_source_and_test_roots(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    checks = tmp_path / "checks" / "unit"
    tests = tmp_path / "tests"
    lib.mkdir()
    checks.mkdir(parents=True)
    tests.mkdir()
    (lib / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")
    (checks / "test_service.py").write_text(
        "def test_service() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    (tests / "test_service.py").write_text(
        "def test_other_service() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    report = run_asp_python(
        tmp_path,
        config=AspPythonConfig(
            source_dir_names=("lib",),
            test_dir_names=("checks",),
        ),
    )

    assert report.is_clean
    assert sorted(module.path for module in report.modules) == [
        str(checks / "test_service.py"),
        str(lib / "service.py"),
        str(tests / "test_service.py"),
    ]
    assert report.project_resolution is not None
    assert report.project_resolution.source_paths == (lib,)
    assert report.project_resolution.test_paths == (checks.parent,)


def test_project_runner_parameters_override_configured_roots(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    src = tmp_path / "src"
    lib.mkdir()
    src.mkdir()
    (lib / "included.py").write_text('"""Included docs."""\n', encoding="utf-8")
    (src / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")

    report = run_asp_python(
        tmp_path,
        config=AspPythonConfig(source_dir_names=("lib",)),
        source_dir_names=("src",),
        include_tests=False,
    )

    assert report.is_clean
    assert [module.path for module in report.modules] == [
        str(lib / "included.py"),
        str(src / "service.py"),
    ]
    assert report.project_resolution is not None
    assert report.project_resolution.source_paths == (src,)


def test_project_runner_parameters_override_configured_extra_paths(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    examples = tmp_path / "examples"
    tools = tmp_path / "tools"
    src.mkdir()
    examples.mkdir()
    tools.mkdir()
    (src / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")
    (examples / "demo.py").write_text('"""Example docs."""\n', encoding="utf-8")
    (tools / "check.py").write_text('"""Check docs."""\n', encoding="utf-8")

    report = run_asp_python(
        tmp_path,
        config=AspPythonConfig(extra_path_names=("examples",)),
        extra_path_names=("tools",),
    )

    assert report.is_clean
    assert sorted(module.path for module in report.modules) == [
        str(examples / "demo.py"),
        str(src / "service.py"),
        str(tools / "check.py"),
    ]
    assert report.project_resolution is not None
    assert report.project_resolution.extra_paths == (tools,)


def test_project_runner_can_exclude_tests_from_config(tmp_path: Path) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    report = run_asp_python(
        tmp_path,
        config=AspPythonConfig(include_tests=False),
    )

    assert report.is_clean
    assert [module.path for module in report.modules] == [str(src / "service.py")]
    assert report.project_resolution is not None
    assert report.project_resolution.test_paths == (tests.parent,)
    assert report.project_resolution.monitored_paths == (src,)


def test_project_runner_can_disable_policy_rules_from_config(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )

    report = run_asp_python(
        tmp_path,
        config=AspPythonConfig(disabled_rule_ids=frozenset({"PY-MOD-R002"})),
    )

    assert report.is_clean
    assert "PY-MOD-R002" not in {finding.rule_id for finding in report.findings}
    assert report.disabled_rule_ids == frozenset({"PY-MOD-R002"})


def test_project_runner_loads_policy_config_from_pyproject(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.asp-python]
disabled_rule_ids = ["PY-MOD-R002"]
""".lstrip(),
        encoding="utf-8",
    )
    (src / "service.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert report.is_clean
    assert report.disabled_rule_ids == frozenset({"PY-MOD-R002"})


def test_explicit_project_config_overrides_pyproject_policy_config(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.asp-python]
disabled_rule_ids = ["PY-MOD-R002"]
""".lstrip(),
        encoding="utf-8",
    )
    (src / "service.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path, config=AspPythonConfig())

    assert not report.is_clean
    assert report.disabled_rule_ids == frozenset()


def test_project_runner_can_promote_policy_rules_from_config(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        "def build(value):\n    return value\n",
        encoding="utf-8",
    )

    report = run_asp_python(
        tmp_path,
        config=AspPythonConfig(blocking_rule_ids=frozenset({"PY-AGENT-POLICY-001"})),
    )

    assert not report.is_clean
    assert [finding.rule_id for finding in report.blocking_findings()] == [
        "PY-AGENT-POLICY-001",
    ]
    assert report.blocking_rule_ids == frozenset({"PY-AGENT-POLICY-001"})


def test_runner_rejects_missing_project_root_and_explicit_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    try:
        run_asp_python(missing)
    except ValueError as error:
        assert str(error) == f"project root does not exist: {missing}"
    else:
        raise AssertionError("missing project root should fail")

    try:
        run_python_lang_harness([missing])
    except ValueError as error:
        assert str(error) == f"harness path does not exist: {missing}"
    else:
        raise AssertionError("missing harness path should fail")
