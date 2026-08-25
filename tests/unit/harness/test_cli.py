from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING

from python_lang_project_harness import run_cli

if TYPE_CHECKING:
    from pathlib import Path


def test_cli_help_advertises_exact_projection_routes() -> None:
    stdout = io.StringIO()
    exit_code = run_cli(["--help"], stdout=stdout)
    rendered = stdout.getvalue()
    assert exit_code == 0
    assert "asp-python search <view> ... [--json] [--package PATH]" in rendered
    assert (
        "asp python query --selector <exact-structural-selector> "
        "--projection <source|callable-skeleton>" in rendered
    )


def test_cli_subcommand_help_advertises_exact_projection() -> None:
    for args in (["search", "--help"], ["query", "--help"]):
        stdout = io.StringIO()
        exit_code = run_cli(args, stdout=stdout)
        rendered = stdout.getvalue()
        assert exit_code == 0
        assert "--selector <exact-structural-selector>" in rendered
        assert "--projection <source|callable-skeleton>" in rendered


def test_cli_agent_guide_advertises_exact_source_route(tmp_path: Path) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "guide", str(tmp_path)], stdout=stdout)
    rendered = stdout.getvalue()

    assert exit_code == 0
    assert (
        "asp python query --selector <exact-structural-selector> "
        "--projection source --workspace <workspace-root>" in rendered
    )


def test_cli_renders_compact_text_by_default(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Package docs."""\n', encoding="utf-8")

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli([str(tmp_path)], stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert stdout.getvalue().startswith("[ok] . python")
    assert "Files: 1 Parsed: 1" in stdout.getvalue()
    assert str(tmp_path) not in stdout.getvalue()


def test_cli_json_flag_renders_structured_report(tmp_path: Path) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Package docs."""\n', encoding="utf-8")
    stdout = io.StringIO()

    exit_code = run_cli(["--json", str(tmp_path)], stdout=stdout)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["is_clean"] is True
    assert payload["file_count"] == 1
    assert payload["project_resolution"]["project_root"] == str(tmp_path)


def test_cli_agent_snapshot_renders_parser_backed_project_shape(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Package docs."""\n', encoding="utf-8")
    stdout = io.StringIO()

    exit_code = run_cli(["--agent-snapshot", str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    rendered = stdout.getvalue()
    assert rendered.startswith("[agent-snapshot] . python\n")
    assert "[tree] . python" in rendered
    assert "Modules: source=1" in rendered
    assert "[nodes]" not in rendered
    assert "[ok]" not in rendered
    assert str(tmp_path) not in rendered


def test_cli_keeps_agent_advice_non_blocking(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        "def build(value):\n    return value\n", encoding="utf-8"
    )
    stdout = io.StringIO()

    exit_code = run_cli([str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    assert "[advice]" in stdout.getvalue()
    assert "PY-AGENT-POLICY-001" in stdout.getvalue()


def test_cli_exits_nonzero_for_blocking_findings(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        'def build() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli([str(tmp_path)], stdout=stdout)

    assert exit_code == 1
    assert "PY-MOD-R002" in stdout.getvalue()
    assert stdout.getvalue().startswith("[fail] python")
    assert "severity=warning" in stdout.getvalue()
    assert "src/service.py" in stdout.getvalue()
    assert str(tmp_path) not in stdout.getvalue()


def test_cli_can_disable_policy_rule_ids(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        ["--disable-rule", "PY-MOD-R002", str(tmp_path)],
        stdout=stdout,
    )

    assert exit_code == 0
    assert "PY-MOD-R002" not in stdout.getvalue()


def test_cli_loads_project_policy_config_from_pyproject(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.python-lang-project-harness]
disabled_rule_ids = ["PY-MOD-R002"]
""".lstrip(),
        encoding="utf-8",
    )
    (src / "service.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli([str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    assert "PY-MOD-R002" not in stdout.getvalue()


def test_cli_uses_pyproject_declared_package_source_scope(tmp_path: Path) -> None:
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
    (package / "__init__.py").write_text(
        '"""Package public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    (tests / "test_tools.py").write_text(
        "def test_tools() -> None:\n    assert True\n",
        encoding="utf-8",
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
    stdout = io.StringIO()

    exit_code = run_cli(["--json", str(tmp_path)], stdout=stdout)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["is_clean"] is True
    assert [finding["rule_id"] for finding in payload["findings"]] == []
    assert payload["project_resolution"]["source_paths"] == [str(package_source)]
    assert payload["project_resolution"]["project_paths"] == [
        str(package_source),
        str(tmp_path / "tests"),
    ]


def test_cli_can_promote_policy_rule_ids(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        "def build(value):\n    return value\n",
        encoding="utf-8",
    )
    stdout = io.StringIO()

    exit_code = run_cli(
        ["--block-rule", "PY-AGENT-POLICY-001", str(tmp_path)], stdout=stdout
    )

    assert exit_code == 1
    assert "PY-AGENT-POLICY-001" in stdout.getvalue()
    assert stdout.getvalue().startswith("[fail] python")
    assert "severity=info" in stdout.getvalue()


def test_cli_help_and_argument_errors_are_stable(tmp_path: Path) -> None:
    help_stdout = io.StringIO()
    error_stderr = io.StringIO()

    assert run_cli(["--help"], stdout=help_stdout) == 0
    assert "asp-python search <view>" in help_stdout.getvalue()
    assert (
        "asp-python [--json | --agent-snapshot] [--no-tests]" in help_stdout.getvalue()
    )
    assert run_cli(["--bogus"], stderr=error_stderr) == 2
    assert "unknown option: --bogus" in error_stderr.getvalue()
    assert run_cli([str(tmp_path), str(tmp_path)], stderr=io.StringIO()) == 2
    mutually_exclusive_stderr = io.StringIO()
    assert (
        run_cli(
            ["--json", "--agent-snapshot", str(tmp_path)],
            stderr=mutually_exclusive_stderr,
        )
        == 2
    )
    assert "mutually exclusive" in mutually_exclusive_stderr.getvalue()


def test_cli_scope_flags_customize_project_paths(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    tools = tmp_path / "tools"
    tests = tmp_path / "tests" / "unit"
    lib.mkdir()
    tools.mkdir()
    tests.mkdir(parents=True)
    (lib / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")
    (tools / "check.py").write_text('"""Check docs."""\n', encoding="utf-8")
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    stdout = io.StringIO()

    exit_code = run_cli(
        [
            "--source-dir",
            "lib",
            "--extra-path",
            "tools",
            "--no-tests",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    assert "Files: 2 Parsed: 2" in stdout.getvalue()
    assert "[ok] lib, tools python" in stdout.getvalue()


def test_cli_no_tests_skips_test_parser_discovery(tmp_path: Path) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    stdout = io.StringIO()

    exit_code = run_cli(["--no-tests", str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    assert "Files: 1 Parsed: 1" in stdout.getvalue()


def test_cli_scope_flag_values_are_required() -> None:
    stderr = io.StringIO()

    assert run_cli(["--source-dir"], stderr=stderr) == 2
    assert "missing value for --source-dir" in stderr.getvalue()
    assert run_cli(["--disable-rule"], stderr=io.StringIO()) == 2


def test_cli_defaults_to_current_working_directory(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text('"""Service docs."""\n', encoding="utf-8")
    stdout = io.StringIO()

    exit_code = run_cli((), stdout=stdout, cwd=tmp_path)

    assert exit_code == 0
    assert stdout.getvalue().startswith("[ok] . python")
    assert str(tmp_path) not in stdout.getvalue()
