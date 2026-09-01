from __future__ import annotations

from pathlib import Path

from asp_python import (
    PythonOwnerResponsibility,
    PythonVerificationEvidence,
    PythonVerificationProfileHint,
    PythonVerificationReceipt,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTaskKind,
    build_python_verification_performance_index,
    default_python_harness_config,
    plan_python_project_verification_with_config,
)


def test_python_package_microbench_gate_is_verification_owned(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    config = (
        default_python_harness_config()
        .with_verification_profile_hint(
            PythonVerificationProfileHint(
                "src/pkg/api.py",
                (PythonOwnerResponsibility.PUBLIC_API,),
            )
            .with_task_kinds((PythonVerificationTaskKind.PERFORMANCE,))
            .with_rationale("query/search fast paths are latency-sensitive")
        )
        .with_verification_skill_binding(
            PythonVerificationTaskKind.PERFORMANCE,
            PythonVerificationSkillBinding(
                "python-verification-performance",
                "microbench",
            ),
        )
        .with_verification_skill_descriptor(
            PythonVerificationSkillDescriptor.performance()
        )
    )
    plan = plan_python_project_verification_with_config(tmp_path, config)
    performance_index = build_python_verification_performance_index(plan)
    task = plan.active_tasks[0]
    receipt = PythonVerificationReceipt(
        task.fingerprint,
        summary="python perf/query_search_microbench.py passed",
    ).with_evidence(
        (
            PythonVerificationEvidence(
                "benchmark_command",
                "python perf/query_search_microbench.py",
            ),
        )
    )
    satisfied_plan = plan_python_project_verification_with_config(
        tmp_path,
        config.with_verification_receipt(receipt),
    )

    assert performance_index["tasks"] == [
        {
            "fingerprint": task.fingerprint,
            "owner_path": "src/pkg/api.py",
            "why": "performance=owner profile requests verification",
        }
    ]
    assert task.skill_binding is not None
    assert (
        task.skill_binding.dispatch_hint == "python-verification-performance@microbench"
    )
    assert satisfied_plan.tasks[0].receipt == receipt


def _write_public_api_project(project_root: Path) -> None:
    package = project_root / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package docs."""\n__all__ = ["build"]\nfrom .api import build\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text(
        '"""Public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        """
[project]
name = "pkg"
requires-python = ">=3.12"
import-names = ["pkg"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pkg"]
""".lstrip(),
        encoding="utf-8",
    )
