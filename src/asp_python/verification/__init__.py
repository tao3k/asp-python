"""Public verification planning surface for Python project harnesses."""

from __future__ import annotations

from typing import Any

from .model import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationEvidence,
    PythonVerificationPhase,
    PythonVerificationPlan,
    PythonVerificationPolicy,
    PythonVerificationProfileCandidate,
    PythonVerificationProfileHint,
    PythonVerificationProfileIndex,
    PythonVerificationReceipt,
    PythonVerificationReportObligation,
    PythonVerificationReportPersistence,
    PythonVerificationRequirement,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTask,
    PythonVerificationTaskContract,
    PythonVerificationTaskKind,
    PythonVerificationTaskState,
    PythonVerificationWaiver,
)

_LAZY_EXPORTS = {
    "build_python_verification_performance_index": ".indices",
    "build_python_verification_profile_index": ".profile_index",
    "build_python_verification_profile_index_report": ".profile_index",
    "build_python_verification_profile_index_with_config": ".profile_index",
    "build_python_verification_task_index": ".indices",
    "plan_python_project_verification": ".planner",
    "plan_python_project_verification_report": ".planner",
    "plan_python_project_verification_with_config": ".planner",
    "render_python_verification_performance_index_json": ".render",
    "render_python_verification_plan": ".render",
    "render_python_verification_plan_json": ".render",
    "render_python_verification_profile_index": ".render",
    "render_python_verification_profile_index_json": ".render",
    "render_python_verification_skill_contracts": ".render",
    "render_python_verification_task_index_json": ".render",
    "PythonVerificationReportArtifact": ".report",
    "PythonVerificationReportBundle": ".report",
    "PythonVerificationReportWriteConfig": ".report",
    "PythonVerificationReportWriteReceipt": ".report",
    "build_python_verification_report_bundle": ".report",
    "render_python_verification_report_artifact_json": ".report",
    "render_python_verification_report_bundle_json": ".report",
    "write_python_verification_reports": ".report",
}


def __getattr__(name: str) -> Any:
    """Load planner/render/report exports lazily to keep model imports acyclic."""

    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    from importlib import import_module

    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "PythonOwnerResponsibility",
    "PythonVerificationDependencySignal",
    "PythonVerificationEvidence",
    "PythonVerificationPhase",
    "PythonVerificationPlan",
    "PythonVerificationPolicy",
    "PythonVerificationProfileCandidate",
    "PythonVerificationProfileHint",
    "PythonVerificationProfileIndex",
    "PythonVerificationReceipt",
    "PythonVerificationReportArtifact",
    "PythonVerificationReportBundle",
    "PythonVerificationReportObligation",
    "PythonVerificationReportPersistence",
    "PythonVerificationReportWriteConfig",
    "PythonVerificationReportWriteReceipt",
    "PythonVerificationRequirement",
    "PythonVerificationSkillBinding",
    "PythonVerificationSkillDescriptor",
    "PythonVerificationTask",
    "PythonVerificationTaskContract",
    "PythonVerificationTaskKind",
    "PythonVerificationTaskState",
    "PythonVerificationWaiver",
    "build_python_verification_performance_index",
    "build_python_verification_profile_index",
    "build_python_verification_profile_index_report",
    "build_python_verification_profile_index_with_config",
    "build_python_verification_report_bundle",
    "build_python_verification_task_index",
    "plan_python_project_verification",
    "plan_python_project_verification_report",
    "plan_python_project_verification_with_config",
    "render_python_verification_performance_index_json",
    "render_python_verification_plan",
    "render_python_verification_plan_json",
    "render_python_verification_profile_index",
    "render_python_verification_profile_index_json",
    "render_python_verification_report_artifact_json",
    "render_python_verification_report_bundle_json",
    "render_python_verification_skill_contracts",
    "render_python_verification_task_index_json",
    "write_python_verification_reports",
]
