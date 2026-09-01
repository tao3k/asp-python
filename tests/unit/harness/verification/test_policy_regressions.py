from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationProfileHint,
    PythonVerificationTaskKind,
    default_python_harness_config,
    plan_python_project_verification_with_config,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_dependency_signal_uses_pep503_distribution_names(
    tmp_path: Path,
) -> None:
    _write_public_api_project(
        tmp_path,
        dependencies='dependencies = ["zope.interface>=6"]',
    )
    config = default_python_harness_config().with_verification_dependency_signal(
        PythonVerificationDependencySignal(
            "zope-interface",
            (PythonOwnerResponsibility.NETWORK,),
            task_kinds=(PythonVerificationTaskKind.STRESS,),
        )
    )

    plan = plan_python_project_verification_with_config(tmp_path, config)

    assert len(plan.active_tasks) == 1
    assert plan.active_tasks[0].owner_path == "pyproject.toml"
    assert plan.active_tasks[0].kind == PythonVerificationTaskKind.STRESS
    assert "zope.interface" in {
        evidence.value for evidence in plan.active_tasks[0].evidence
    }


def test_profile_hint_uses_configured_responsibility_task_mapping(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    base_config = default_python_harness_config()
    policy = base_config.verification_policy.with_responsibility_task_kinds(
        PythonOwnerResponsibility.PUBLIC_API,
        (PythonVerificationTaskKind.SECURITY,),
    )
    config = base_config.with_verification_policy(
        policy
    ).with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/api.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        ).with_task_kinds((PythonVerificationTaskKind.SECURITY,))
    )

    plan = plan_python_project_verification_with_config(tmp_path, config)

    assert [task.kind for task in plan.active_tasks] == [
        PythonVerificationTaskKind.SECURITY,
    ]


def _write_public_api_project(
    project_root: Path,
    *,
    dependencies: str = "",
) -> None:
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
    dependency_line = "" if not dependencies else f"{dependencies}\n"
    (project_root / "pyproject.toml").write_text(
        f"""
[project]
name = "pkg"
requires-python = ">=3.12"
import-names = ["pkg"]
{dependency_line}
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pkg"]
""".lstrip(),
        encoding="utf-8",
    )
