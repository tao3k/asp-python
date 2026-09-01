"""Parser-backed verification planner for Python project harnesses."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from .._model import AspPythonConfig, AspPythonReport
from .._render import _render_display_path
from .._rule_packs import resolve_project_harness_config
from .._runner import run_asp_python
from .facts import (
    matched_dependency_signals,
    node_evidence,
    parser_visible_owner_responsibilities,
    project_metadata_owner_path,
    require_dependency_name,
    verification_fingerprint,
    verification_project_root,
    verification_reasoning_tree_facts,
)
from .model import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationEvidence,
    PythonVerificationPlan,
    PythonVerificationPolicy,
    PythonVerificationProfileHint,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTask,
    PythonVerificationTaskContract,
    PythonVerificationTaskKind,
    PythonVerificationTaskState,
)
from .obligations import verification_report_obligations

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeNode


def plan_python_project_verification(
    project_root: str | Path,
) -> PythonVerificationPlan:
    """Plan external verification obligations for one Python project."""

    return plan_python_project_verification_with_config(project_root, None)


def plan_python_project_verification_with_config(
    project_root: str | Path,
    config: AspPythonConfig | None,
) -> PythonVerificationPlan:
    """Plan verification obligations with an explicit harness config."""

    root = Path(project_root)
    selected_config = resolve_project_harness_config(root, config, rule_packs=None)
    report = run_asp_python(root, config=selected_config)
    return plan_python_project_verification_report(report, selected_config)


def plan_python_project_verification_report(
    report: AspPythonReport,
    config: AspPythonConfig,
) -> PythonVerificationPlan:
    """Plan verification obligations from an already-built harness report."""

    project_root = verification_project_root(report)
    policy = config.verification_policy
    facts = verification_reasoning_tree_facts(report)
    node_by_path = {
        _render_display_path(node.path, project_root=project_root): node
        for node in facts.nodes
    }
    owner_responsibilities_by_path = parser_visible_owner_responsibilities(
        facts,
        project_root=project_root,
        dependency_signals=policy.dependency_signals,
    )
    tasks: list[PythonVerificationTask] = []
    seen: set[tuple[str, PythonVerificationTaskKind, str]] = set()
    for hint in policy.profile_hints:
        tasks.extend(
            _tasks_for_profile_hint(
                hint,
                node_by_path=node_by_path,
                parser_responsibilities=owner_responsibilities_by_path.get(
                    hint.owner_path,
                    (),
                ),
                policy=policy,
                seen=seen,
            )
        )
    metadata = facts.project_metadata
    if metadata is not None:
        metadata_owner_path = project_metadata_owner_path(
            facts,
            project_root=project_root,
        )
        for dependency, signal in matched_dependency_signals(
            metadata.dependencies,
            policy.dependency_signals,
        ):
            if metadata_owner_path is None:
                continue
            tasks.extend(
                _tasks_for_dependency_signal(
                    owner_path=metadata_owner_path,
                    dependency=require_dependency_name(dependency),
                    signal=signal,
                    policy=policy,
                    seen=seen,
                )
            )
    tasks = [_apply_receipts_and_waivers(task, policy=policy) for task in tasks]
    active_tasks = tuple(task for task in tasks if task.is_active)
    return PythonVerificationPlan(
        project_root=project_root,
        tasks=tuple(tasks),
        report_obligations=verification_report_obligations(active_tasks),
    )


def _tasks_for_profile_hint(
    hint: PythonVerificationProfileHint,
    *,
    node_by_path: dict[str, PythonReasoningTreeNode],
    parser_responsibilities: tuple[PythonOwnerResponsibility, ...],
    policy: PythonVerificationPolicy,
    seen: set[tuple[str, PythonVerificationTaskKind, str]],
) -> tuple[PythonVerificationTask, ...]:
    node = node_by_path.get(hint.owner_path)
    review_reason = _profile_hint_review_reason(
        hint,
        node,
        parser_responsibilities=parser_responsibilities,
        policy=policy,
    )
    if review_reason is not None:
        task = _task(
            owner_path=hint.owner_path,
            owner_namespace=() if node is None else node.namespace,
            responsibilities=hint.responsibilities,
            kind=PythonVerificationTaskKind.RESPONSIBILITY_REVIEW,
            why=review_reason,
            evidence=(),
            policy=policy,
            seen=seen,
        )
        return () if task is None else (task,)
    if not hint.verification_tasks_enabled:
        return ()
    task_kinds = hint.task_kinds or policy.task_kinds_for_responsibilities(
        hint.responsibilities
    )
    tasks: list[PythonVerificationTask] = []
    for kind in task_kinds:
        task = _task(
            owner_path=hint.owner_path,
            owner_namespace=() if node is None else node.namespace,
            responsibilities=hint.responsibilities,
            kind=kind,
            why=f"{kind.value}=owner profile requests verification",
            evidence=() if node is None else node_evidence(node),
            contract=hint.task_contracts.get(kind),
            policy=policy,
            seen=seen,
        )
        if task is not None:
            tasks.append(task)
    return tuple(tasks)


def _tasks_for_dependency_signal(
    *,
    owner_path: str,
    dependency: str,
    signal: PythonVerificationDependencySignal,
    policy: PythonVerificationPolicy,
    seen: set[tuple[str, PythonVerificationTaskKind, str]],
) -> tuple[PythonVerificationTask, ...]:
    task_kinds = signal.task_kinds or policy.task_kinds_for_responsibilities(
        signal.responsibilities
    )
    tasks: list[PythonVerificationTask] = []
    for kind in task_kinds:
        task = _task(
            owner_path=owner_path,
            owner_namespace=(),
            responsibilities=signal.responsibilities,
            kind=kind,
            why=f"{kind.value}=dependency {dependency} maps to verification responsibility",
            evidence=(PythonVerificationEvidence("dependency", dependency),),
            policy=policy,
            seen=seen,
        )
        if task is not None:
            tasks.append(task)
    return tuple(tasks)


def _task(
    *,
    owner_path: str,
    owner_namespace: tuple[str, ...],
    responsibilities: tuple[PythonOwnerResponsibility, ...],
    kind: PythonVerificationTaskKind,
    why: str,
    evidence: tuple[PythonVerificationEvidence, ...],
    contract: PythonVerificationTaskContract | None = None,
    policy: PythonVerificationPolicy,
    seen: set[tuple[str, PythonVerificationTaskKind, str]],
) -> PythonVerificationTask | None:
    key = (
        owner_path,
        kind,
        ",".join(sorted(responsibility.value for responsibility in responsibilities)),
    )
    if key in seen:
        return None
    seen.add(key)
    skill_binding = policy.skill_bindings.get(kind)
    skill_descriptor = _skill_descriptor_for(
        kind,
        skill_binding=skill_binding,
        policy=policy,
    )
    binding_label = "" if skill_binding is None else skill_binding.dispatch_hint
    descriptor_label = (
        "" if skill_descriptor is None else skill_descriptor.compact_label
    )
    fingerprint = verification_fingerprint(
        owner_path,
        kind,
        why,
        binding_label=binding_label,
        descriptor_label=descriptor_label,
    )
    selected_contract = (
        contract
        or policy.task_contracts.get(kind)
        or PythonVerificationTaskContract.default_for(kind)
    )
    return PythonVerificationTask(
        owner_path=owner_path,
        owner_namespace=owner_namespace,
        responsibilities=responsibilities,
        kind=kind,
        state=PythonVerificationTaskState.PENDING,
        phase=selected_contract.phase,
        fingerprint=fingerprint,
        why=why,
        contract=selected_contract,
        evidence=evidence,
        skill_binding=skill_binding,
        skill_descriptor=skill_descriptor,
    )


def _apply_receipts_and_waivers(
    task: PythonVerificationTask,
    *,
    policy: PythonVerificationPolicy,
) -> PythonVerificationTask:
    receipt = next(
        (
            receipt
            for receipt in policy.receipts
            if receipt.task_fingerprint == task.fingerprint
        ),
        None,
    )
    if receipt is not None:
        return replace(
            task,
            state=PythonVerificationTaskState.SATISFIED,
            receipt=receipt,
        )
    waiver = next(
        (
            waiver
            for waiver in policy.waivers
            if waiver.task_fingerprint == task.fingerprint and waiver.is_complete
        ),
        None,
    )
    if waiver is not None:
        return replace(task, state=PythonVerificationTaskState.WAIVED, waiver=waiver)
    return task


def _profile_hint_review_reason(
    hint: PythonVerificationProfileHint,
    node: PythonReasoningTreeNode | None,
    *,
    parser_responsibilities: tuple[PythonOwnerResponsibility, ...],
    policy: PythonVerificationPolicy,
) -> str | None:
    if node is None and not parser_responsibilities:
        return "responsibility_review=profile owner path is not parser-visible"
    if not hint.verification_tasks_enabled and not hint.rationale.strip():
        return "responsibility_review=owner-local verification suppression needs compact rationale"
    if (
        (hint.task_kinds or hint.task_contracts)
        and not hint.rationale.strip()
        and (
            set(hint.task_kinds)
            != set(policy.task_kinds_for_responsibilities(hint.responsibilities))
            or bool(hint.task_contracts)
        )
    ):
        return "responsibility_review=owner-local verification override needs compact rationale"
    owner_responsibilities = set(parser_responsibilities)
    missing = tuple(
        responsibility
        for responsibility in hint.responsibilities
        if responsibility not in owner_responsibilities
    )
    if missing:
        return (
            "responsibility_review=profile responsibility does not match parser facts"
        )
    return None


def _skill_descriptor_for(
    kind: PythonVerificationTaskKind,
    *,
    skill_binding: PythonVerificationSkillBinding | None,
    policy: PythonVerificationPolicy,
) -> PythonVerificationSkillDescriptor | None:
    if skill_binding is not None:
        descriptor = policy.skill_descriptors.get(skill_binding.dispatch_hint)
        if descriptor is not None:
            return descriptor
        descriptor = policy.skill_descriptors.get(skill_binding.skill)
        if descriptor is not None:
            return descriptor
    return next(
        (
            descriptor
            for descriptor in policy.skill_descriptors.values()
            if descriptor.task_kind == kind
            and (
                skill_binding is None
                or descriptor.adapter is None
                or descriptor.adapter == skill_binding.adapter
            )
        ),
        None,
    )
