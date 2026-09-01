"""Compact indexes derived from Python verification plans."""

from __future__ import annotations

from .model import PythonVerificationPlan, PythonVerificationTaskKind


def build_python_verification_task_index(
    plan: PythonVerificationPlan,
) -> dict[str, object]:
    """Return a compact task-index JSON shape for active tasks."""

    return {
        "project_root": str(plan.project_root),
        "tasks": [
            {
                "fingerprint": task.fingerprint,
                "owner_path": task.owner_path,
                "kind": task.kind.value,
                "state": task.state.value,
                "phase": task.phase.value,
            }
            for task in plan.active_tasks
        ],
    }


def build_python_verification_performance_index(
    plan: PythonVerificationPlan,
) -> dict[str, object]:
    """Return a compact index of active performance verification tasks."""

    return {
        "project_root": str(plan.project_root),
        "tasks": [
            {
                "fingerprint": task.fingerprint,
                "owner_path": task.owner_path,
                "why": task.why,
            }
            for task in plan.active_tasks
            if task.kind == PythonVerificationTaskKind.PERFORMANCE
        ],
    }
