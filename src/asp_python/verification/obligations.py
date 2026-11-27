"""Report obligations for active Python verification tasks."""

from __future__ import annotations

from .model import (
    PythonVerificationReportObligation,
    PythonVerificationReportPersistence,
    PythonVerificationTask,
    PythonVerificationTaskKind,
)


def verification_report_obligations(
    active_tasks: tuple[PythonVerificationTask, ...],
) -> tuple[PythonVerificationReportObligation, ...]:
    """Return report artifacts required by active verification work."""

    if not active_tasks:
        return ()
    task_kinds = tuple(
        sorted({task.kind for task in active_tasks}, key=lambda item: item.value)
    )
    obligations = [
        PythonVerificationReportObligation(
            key="verification_plan_json",
            renderer="render_python_verification_plan_json",
            artifact="verification_plan.json",
            task_kinds=task_kinds,
            persistence=PythonVerificationReportPersistence.RUNTIME_CACHE,
        ),
        PythonVerificationReportObligation(
            key="task_index_json",
            renderer=(
                "build_python_verification_task_index + "
                "render_python_verification_task_index_json"
            ),
            artifact="verification_task_index.json",
            task_kinds=task_kinds,
            persistence=PythonVerificationReportPersistence.SOURCE_BASELINE,
        ),
    ]
    if any(
        task.kind == PythonVerificationTaskKind.PERFORMANCE for task in active_tasks
    ):
        obligations.append(
            PythonVerificationReportObligation(
                key="performance_index_json",
                renderer=(
                    "build_python_verification_performance_index + "
                    "render_python_verification_performance_index_json"
                ),
                artifact="performance_index.json",
                task_kinds=(PythonVerificationTaskKind.PERFORMANCE,),
                persistence=PythonVerificationReportPersistence.SOURCE_BASELINE,
            )
        )
    return tuple(obligations)
