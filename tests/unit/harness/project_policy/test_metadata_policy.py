from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import run_asp_python

if TYPE_CHECKING:
    from pathlib import Path


def test_project_policy_blocks_project_table_without_name(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
requires-python = ">=3.12"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""",
    )

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-005", str(tmp_path / "pyproject.toml")),
    ]


def test_project_policy_blocks_project_table_without_requires_python(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""",
    )

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-006", str(tmp_path / "pyproject.toml")),
    ]


def test_project_policy_blocks_build_system_table_without_requires(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[build-system]
build-backend = "hatchling.build"
""",
    )

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-007", str(tmp_path / "pyproject.toml")),
    ]


def test_project_policy_allows_tool_only_pyproject(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
""",
    )

    report = run_asp_python(tmp_path)

    assert not any(
        finding.rule_id.startswith("PY-PROJ-") for finding in report.findings
    )


def test_project_policy_requires_pytest_gate_for_harness_dev_dependency(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]
""",
    )

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-PROJECT-010", str(tmp_path / "pyproject.toml")),
    ]


def test_project_policy_accepts_pytest_addopts_gate(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--python-project-harness"]
""",
    )

    report = run_asp_python(tmp_path)

    assert not any(
        finding.rule_id == "PY-AGENT-PROJECT-010" for finding in report.findings
    )


def test_project_policy_accepts_explicit_pytest_helper_gate(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]
""",
    )
    tests = tmp_path / "tests" / "unit"
    tests.mkdir(parents=True)
    (tests / "test_harness_policy.py").write_text(
        "from asp_python.pytest import asp_python_test\n"
        "test_asp_python_policy = asp_python_test()\n",
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert not any(
        finding.rule_id == "PY-AGENT-PROJECT-010" for finding in report.findings
    )


def test_project_policy_advises_missing_verification_profile_hints(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--python-project-harness"]
""",
    )
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package docs."""\nfrom .api import build\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text(
        '"""API docs."""\n\n\ndef build() -> str:\n    return "ok"\n',
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)
    finding = next(
        finding
        for finding in report.findings
        if finding.rule_id == "PY-AGENT-PROJECT-011"
    )

    assert finding.severity.value == "info"
    assert "parser-visible verification owner candidates" in finding.summary
    assert finding not in report.blocking_findings()


def test_project_policy_accepts_configured_verification_profile_hint(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
[project]
name = "example-pkg"
requires-python = ">=3.12"

[dependency-groups]
test = [
    "asp-python[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--python-project-harness"]

[tool.asp-python.verification]
profile_hints = [
  { owner_path = "src/pkg/__init__.py", responsibilities = ["public_api"], task_kinds = ["regression"], rationale = "package facade" },
]
""",
    )
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package docs."""\nfrom .api import build\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text(
        '"""API docs."""\n\n\ndef build() -> str:\n    return "ok"\n',
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert not any(
        finding.rule_id == "PY-AGENT-PROJECT-011" for finding in report.findings
    )


def _write_pyproject(project_root: Path, content: str) -> None:
    (project_root / "src").mkdir()
    (project_root / "pyproject.toml").write_text(
        content.lstrip(),
        encoding="utf-8",
    )
