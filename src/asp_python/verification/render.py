"""Compact and JSON renderers for Python verification plans."""

from __future__ import annotations

import json

from .indices import (
    build_python_verification_performance_index,
    build_python_verification_task_index,
)
from .model import (
    PythonVerificationPlan,
    PythonVerificationProfileCandidate,
    PythonVerificationProfileIndex,
    PythonVerificationTask,
)


def render_python_verification_plan(plan: PythonVerificationPlan) -> str:
    """Render active verification tasks as compact Agent-facing text."""

    if not plan.active_tasks:
        return ""
    lines = ["[verify]"]
    for task in plan.active_tasks:
        lines.extend(_render_task(task))
    if plan.report_obligations:
        lines.append("[verify-report]")
        for obligation in plan.report_obligations:
            kinds = ",".join(kind.value for kind in obligation.task_kinds)
            lines.append(
                "- required: "
                f"{obligation.key} renderer={obligation.renderer} "
                f"artifact={obligation.artifact} tasks={len(plan.active_tasks)} "
                f"kinds={kinds} persistence={obligation.persistence.value}"
            )
    return "\n".join(lines) + "\n"


def render_python_verification_plan_json(plan: PythonVerificationPlan) -> str:
    """Render a structured verification plan JSON payload."""

    return json.dumps(plan.to_dict(), separators=(",", ":"), sort_keys=True)


def render_python_verification_profile_index(
    index: PythonVerificationProfileIndex,
    *,
    max_candidates: int | None = 24,
) -> str:
    """Render parser-suggested verification profile reminders."""

    candidates = tuple(
        candidate for candidate in index.candidates if candidate.state != "configured"
    )
    if not candidates:
        return ""
    visible_candidates = (
        candidates if max_candidates is None else candidates[:max_candidates]
    )
    sections = []
    if index.needs_profile_configuration():
        sections.append(_render_profile_configuration_reminder(index).rstrip("\n"))
    sections.extend(
        _render_profile_candidate(candidate).rstrip("\n")
        for candidate in visible_candidates
    )
    omitted = len(candidates) - len(visible_candidates)
    if omitted > 0:
        sections.append(f"... +{omitted} verification profile candidates")
    return "\n".join(sections) + "\n"


def _render_profile_configuration_reminder(
    index: PythonVerificationProfileIndex,
) -> str:
    return "\n".join(
        (
            "[verify-profile] profile_hints",
            "   |state: missing_profile_config",
            "   |action: configure PythonVerificationProfileHint entries",
            f"   |candidates: {len(index.active_candidates())}",
        )
    )


def _render_profile_candidate(
    candidate: PythonVerificationProfileCandidate,
) -> str:
    lines = [f"[verify-profile] {candidate.owner_path}"]
    if candidate.owner_namespace:
        lines.append(f"   |owner: {'.'.join(candidate.owner_namespace)}")
    lines.append(f"   |state: {candidate.state}")
    if candidate.configured_responsibilities:
        lines.append(
            "   |configured: "
            + ",".join(
                responsibility.value
                for responsibility in candidate.configured_responsibilities
            )
        )
    lines.append(
        "   |suggest: "
        + ",".join(
            responsibility.value for responsibility in candidate.responsibilities
        )
    )
    lines.append("   |tasks: " + ",".join(kind.value for kind in candidate.task_kinds))
    for evidence in candidate.evidence:
        lines.append(f"   |fact: {evidence.label}={evidence.value}")
    return "\n".join(lines) + "\n"


def render_python_verification_profile_index_json(
    index: PythonVerificationProfileIndex,
) -> str:
    """Render profile-index JSON."""

    return json.dumps(index.to_dict(), separators=(",", ":"), sort_keys=True)


def render_python_verification_task_index_json(plan: PythonVerificationPlan) -> str:
    """Render active verification task-index JSON."""

    return json.dumps(
        build_python_verification_task_index(plan),
        separators=(",", ":"),
        sort_keys=True,
    )


def render_python_verification_performance_index_json(
    plan: PythonVerificationPlan,
) -> str:
    """Render active performance verification index JSON."""

    return json.dumps(
        build_python_verification_performance_index(plan),
        separators=(",", ":"),
        sort_keys=True,
    )


def render_python_verification_skill_contracts(plan: PythonVerificationPlan) -> str:
    """Render task contracts as a compact skill-dispatch tree."""

    if not plan.active_tasks:
        return ""
    lines = ["[verify-contracts]"]
    for task in plan.active_tasks:
        binding = (
            ""
            if task.skill_binding is None
            else f" skill={task.skill_binding.dispatch_hint}"
        )
        contract_ref = (
            ""
            if task.skill_descriptor is None
            else f" contract_ref={task.skill_descriptor.compact_label}"
        )
        lines.append(
            f"- {task.fingerprint}: kind={task.kind.value} "
            f"phase={task.phase.value}{binding}{contract_ref}"
        )
        lines.append(f"  contract: {task.contract.summary}")
        for requirement in task.contract.requirements:
            lines.append(f"  required: {requirement.label}={requirement.detail}")
        if task.skill_descriptor is not None:
            lines.append(f"  descriptor: {task.skill_descriptor.summary}")
            for requirement in task.skill_descriptor.requirements:
                lines.append(
                    f"  descriptor-required: {requirement.label}={requirement.detail}"
                )
    return "\n".join(lines) + "\n"


def _render_task(task: PythonVerificationTask) -> list[str]:
    responsibilities = ",".join(
        responsibility.value for responsibility in task.responsibilities
    )
    binding = (
        ""
        if task.skill_binding is None
        else f" skill={task.skill_binding.dispatch_hint}"
    )
    contract_ref = (
        ""
        if task.skill_descriptor is None
        else f" contract_ref={task.skill_descriptor.compact_label}"
    )
    evidence = " ".join(f"{item.label}={item.value}" for item in task.evidence)
    suffix = "" if not evidence else f" evidence={evidence}"
    return [
        f"- {task.owner_path}: {task.kind.value} {task.state.value} "
        f"phase={task.phase.value} fingerprint={task.fingerprint}{binding}{contract_ref}",
        f"  why: {task.why} responsibilities={responsibilities}{suffix}",
        f"  contract: {task.contract.summary}",
    ]
