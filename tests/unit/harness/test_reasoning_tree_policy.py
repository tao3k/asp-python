from __future__ import annotations

from pathlib import Path

from asp_python import run_asp_python

_PROJECT_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").exists() and (parent / "src").exists()
)


def test_modularity_rule_pack_blocks_shadowed_reasoning_tree_owner(
    tmp_path: Path,
) -> None:
    package = tmp_path / "src" / "pkg"
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

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-MOD-R007", str(shadow_package / "__init__.py")),
    ]
    assert "one source owner" in report.findings[0].requirement


def test_agent_policy_reports_branch_package_without_reasoning_tree_intent(
    tmp_path: Path,
) -> None:
    branch = tmp_path / "src" / "pkg" / "domain"
    branch.mkdir(parents=True)
    (branch / "__init__.py").write_text("", encoding="utf-8")
    (branch / "service.py").write_text('"""Service leaf."""\n', encoding="utf-8")
    (branch / "models.py").write_text('"""Model leaf."""\n', encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-AGENT-POLICY-007", str(branch / "__init__.py")),
    ]
    assert "owner subtree" in report.findings[0].requirement
    assert "package intent docstring" in report.findings[0].label


def test_agent_policy_accepts_documented_reasoning_tree_branch(
    tmp_path: Path,
) -> None:
    branch = tmp_path / "src" / "pkg" / "domain"
    branch.mkdir(parents=True)
    (branch / "__init__.py").write_text(
        '"""Domain package owner."""\n',
        encoding="utf-8",
    )
    (branch / "service.py").write_text('"""Service leaf."""\n', encoding="utf-8")
    (branch / "models.py").write_text('"""Model leaf."""\n', encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert report.is_clean


def test_reasoning_tree_policy_uses_parser_facts() -> None:
    modularity = (_PROJECT_ROOT / "src" / "asp_python" / "_modularity.py").read_text(
        encoding="utf-8"
    )
    agent_reasoning_tree = (
        _PROJECT_ROOT / "src" / "asp_python" / "_agent_reasoning_tree.py"
    ).read_text(encoding="utf-8")

    assert "python_reasoning_tree_facts(" in modularity
    assert "python_reasoning_tree_facts(" in agent_reasoning_tree
    assert 'path.name == "__init__.py"' not in modularity
    assert 'path.name == "__init__.py"' not in agent_reasoning_tree
