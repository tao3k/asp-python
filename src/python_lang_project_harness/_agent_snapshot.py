"""Agent-facing project snapshot renderer for Python harness runs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._agent_snapshot_tree import render_python_agent_snapshot_tree
from ._render import (
    render_python_lang_harness,
)
from ._rule_packs import resolve_project_harness_config
from ._runner import run_python_project_harness
from .verification import (
    build_python_verification_profile_index_report,
    plan_python_project_verification_report,
    render_python_verification_plan,
    render_python_verification_profile_index,
)

if TYPE_CHECKING:
    from ._model import PythonHarnessConfig, PythonHarnessReport


def render_python_project_harness_agent_snapshot(project_root: str | Path) -> str:
    """Render a compact parser-backed project snapshot for repair agents."""

    return render_python_project_harness_agent_snapshot_with_config(
        project_root,
        None,
    )


def render_python_project_harness_agent_snapshot_with_config(
    project_root: str | Path,
    config: PythonHarnessConfig | None,
) -> str:
    """Render an agent snapshot using an explicit harness config."""

    root = Path(project_root)
    selected_config = resolve_project_harness_config(root, config, rule_packs=None)
    report = run_python_project_harness(root, config=selected_config)
    return render_python_project_harness_agent_snapshot_report(
        report,
        config=selected_config,
    )


def render_python_project_harness_agent_snapshot_report(
    report: PythonHarnessReport,
    *,
    config: PythonHarnessConfig | None = None,
) -> str:
    """Render an already-built project harness report as an agent snapshot."""

    project_root = (
        None
        if report.project_resolution is None
        else report.project_resolution.project_root
    )
    target = ", ".join(
        _display_path(Path(path), project_root=project_root)
        for path in report.root_paths
    )
    sections = [f"[agent-snapshot] {target} python"]
    policy = _render_policy_section(report)
    if policy:
        sections.append(policy.rstrip("\n"))
    tree = render_python_agent_snapshot_tree(report, target=target)
    if tree:
        sections.append(tree.rstrip("\n"))
    if config is not None:
        verification_profile = render_python_verification_profile_index(
            build_python_verification_profile_index_report(report, config),
            max_candidates=6,
        )
        if verification_profile:
            sections.append(verification_profile.rstrip("\n"))
        verification = render_python_verification_plan(
            plan_python_project_verification_report(report, config)
        )
        if verification:
            sections.append(verification.rstrip("\n"))
    return "\n".join(sections) + "\n"


def _render_policy_section(report: PythonHarnessReport) -> str:
    rendered = render_python_lang_harness(report)
    if rendered.startswith("[ok]"):
        return ""
    return "[policy]\n" + rendered


def _display_path(path: Path, *, project_root: Path | None) -> str:
    if project_root is None:
        return str(path)
    try:
        return str(
            path.resolve(strict=False).relative_to(project_root.resolve(strict=False))
        )
    except ValueError:
        return str(path)
