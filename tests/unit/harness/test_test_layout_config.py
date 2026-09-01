from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import run_asp_python

if TYPE_CHECKING:
    from pathlib import Path


def test_layout_policy_requires_explanation_for_root_file_exception(
    tmp_path: Path,
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    root_file = tests / "test_contract_gate.py"
    root_file.write_text(
        "def test_contract_gate() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    _write_policy(
        tests,
        """
[tests]
allowed_root_files = [
  { name = "test_contract_gate.py", explanation = "" },
]
""",
    )
    report = run_asp_python(tmp_path)
    assert [finding.rule_id for finding in report.findings] == ["PY-TEST-R001"]

    _write_policy(
        tests,
        """
[tests]
allowed_root_files = [
  { name = "test_contract_gate.py", explanation = "root gate mounts an external contract suite" },
]
""",
    )
    report = run_asp_python(tmp_path)
    assert not any(finding.rule_id == "PY-TEST-R001" for finding in report.findings)


def test_layout_policy_requires_explanation_for_directory_exception(
    tmp_path: Path,
) -> None:
    tests = tmp_path / "tests"
    contract = tests / "contract"
    contract.mkdir(parents=True)
    (contract / "test_contract.py").write_text(
        "def test_contract() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    _write_policy(
        tests,
        """
[tests]
allowed_directories = [
  { name = "contract", explanation = "" },
]
""",
    )
    report = run_asp_python(tmp_path)
    assert [finding.rule_id for finding in report.findings] == ["PY-TEST-R002"]

    _write_policy(
        tests,
        """
[tests]
allowed_directories = [
  { name = "contract", explanation = "contract suite is mounted by CI and kept outside unit" },
]
""",
    )
    report = run_asp_python(tmp_path)
    assert not any(finding.rule_id == "PY-TEST-R002" for finding in report.findings)


def _write_policy(tests_dir: Path, content: str) -> None:
    (tests_dir / "python-project-harness-rules.toml").write_text(
        content.lstrip(),
        encoding="utf-8",
    )
