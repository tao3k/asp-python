from __future__ import annotations

import json
from typing import TYPE_CHECKING

from asp_python import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationPhase,
    PythonVerificationProfileHint,
    PythonVerificationReceipt,
    PythonVerificationReportWriteConfig,
    PythonVerificationRequirement,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTaskContract,
    PythonVerificationTaskKind,
    build_python_verification_profile_index_with_config,
    build_python_verification_report_bundle,
    default_python_harness_config,
    plan_python_project_verification_with_config,
    read_asp_python_config,
    render_asp_python_agent_snapshot_with_config,
    render_python_verification_plan,
    render_python_verification_profile_index,
    render_python_verification_profile_index_json,
    render_python_verification_report_artifact_json,
    render_python_verification_report_bundle_json,
    render_python_verification_skill_contracts,
    write_python_verification_reports,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_verification_profile_hint_plans_external_task(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    config = default_python_harness_config().with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/api.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        )
        .with_task_kinds((PythonVerificationTaskKind.SECURITY,))
        .with_rationale("this public API needs a security review")
    )

    plan = plan_python_project_verification_with_config(tmp_path, config)
    rendered = render_python_verification_plan(plan)

    assert len(plan.active_tasks) == 1
    assert plan.active_tasks[0].kind == PythonVerificationTaskKind.SECURITY
    assert "[verify]" in rendered
    assert "src/pkg/api.py: security pending" in rendered
    assert "[verify-report]" in rendered


def test_verification_receipt_satisfies_matching_task(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    base_config = default_python_harness_config().with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/api.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        )
    )
    pending_plan = plan_python_project_verification_with_config(tmp_path, base_config)
    receipt = PythonVerificationReceipt(
        task_fingerprint=pending_plan.active_tasks[0].fingerprint,
        summary="pytest regression passed",
    )

    satisfied_plan = plan_python_project_verification_with_config(
        tmp_path,
        base_config.with_verification_receipt(receipt),
    )

    assert satisfied_plan.active_tasks == ()
    assert render_python_verification_plan(satisfied_plan) == ""
    assert satisfied_plan.tasks[0].receipt == receipt


def test_verification_profile_index_uses_parser_and_dependency_facts(
    tmp_path: Path,
) -> None:
    _write_public_api_project(
        tmp_path,
        dependencies='dependencies = ["httpx>=0.28"]',
    )
    config = default_python_harness_config().with_verification_dependency_signal(
        PythonVerificationDependencySignal(
            "httpx",
            (PythonOwnerResponsibility.NETWORK,),
            task_kinds=(PythonVerificationTaskKind.STRESS,),
        )
    )

    index = build_python_verification_profile_index_with_config(tmp_path, config)
    rendered = render_python_verification_profile_index(index)
    profile_payload = json.loads(render_python_verification_profile_index_json(index))
    metadata_hint = next(
        hint
        for hint in index.active_profile_hints()
        if hint.owner_path == "pyproject.toml"
    )
    plan_from_hint = plan_python_project_verification_with_config(
        tmp_path,
        config.with_verification_profile_hint(metadata_hint),
    )

    assert "[verify-profile] src/pkg/api.py" in rendered
    assert "   |state: missing_profile" in rendered
    assert "   |suggest: public_api" in rendered
    assert "[verify-profile] pyproject.toml" in rendered
    assert "   |suggest: network" in rendered
    assert "   |fact: dependency=httpx" in rendered
    assert profile_payload["configured_profile_hint_count"] == 0
    assert profile_payload["needs_profile_configuration"] is True
    assert profile_payload["active_profile_hints"]
    assert len(plan_from_hint.active_tasks) == 1
    assert plan_from_hint.active_tasks[0].owner_path == "pyproject.toml"
    assert plan_from_hint.active_tasks[0].kind == PythonVerificationTaskKind.STRESS


def test_verification_report_bundle_and_writer_emit_modular_artifacts(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    config = default_python_harness_config().with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/api.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        )
        .with_task_kinds((PythonVerificationTaskKind.PERFORMANCE,))
        .with_rationale("this public API is latency-sensitive")
    )
    plan = plan_python_project_verification_with_config(tmp_path, config)

    bundle = json.loads(render_python_verification_report_bundle_json(plan))
    bundle_object = build_python_verification_report_bundle(plan)
    plan_payload = render_python_verification_report_artifact_json(
        plan,
        "verification_plan_json",
    )
    receipt = write_python_verification_reports(
        plan,
        PythonVerificationReportWriteConfig(
            source_baseline_dir=tmp_path / ".harness" / "baseline",
            runtime_cache_dir=tmp_path / ".harness" / "cache",
        ),
    )

    assert [item["artifact"] for item in bundle["artifacts"]] == [
        "verification_plan.json",
        "verification_task_index.json",
        "performance_index.json",
    ]
    assert bundle["project_root"] == str(tmp_path)
    assert [item.artifact for item in bundle_object.source_baseline_artifacts()] == [
        "verification_task_index.json",
        "performance_index.json",
    ]
    assert [item.artifact for item in bundle_object.runtime_cache_artifacts()] == [
        "verification_plan.json",
    ]
    assert bundle_object.artifact("task_index_json") is not None
    assert plan_payload is not None
    assert "performance" in plan_payload
    assert len(receipt.artifact_paths) == 3
    assert all(path.exists() for path in receipt.artifact_paths)
    source_manifest = json.loads(receipt.manifest_paths[0].read_text(encoding="utf-8"))
    runtime_manifest = json.loads(receipt.manifest_paths[1].read_text(encoding="utf-8"))
    assert source_manifest["project_root"] == str(tmp_path)
    assert runtime_manifest["project_root"] == str(tmp_path)
    assert [item["artifact"] for item in source_manifest["artifacts"]] == [
        "verification_task_index.json",
        "performance_index.json",
    ]
    assert [item["artifact"] for item in runtime_manifest["artifacts"]] == [
        "verification_plan.json",
        "verification_task_index.json",
        "performance_index.json",
    ]


def test_verification_policy_can_be_loaded_from_pyproject_config(
    tmp_path: Path,
) -> None:
    _write_public_api_project(
        tmp_path,
        harness_config="""
[tool.asp-python.verification]
profile_hints = [
  { owner_path = "src/pkg/api.py", responsibilities = ["public_api"], task_kinds = ["security"], rationale = "authz-sensitive public API" },
]
dependency_signals = [
  { package_name = "httpx", responsibilities = ["network"], task_kinds = ["stress"] },
]

[tool.asp-python.verification.task_contracts]
security = { phase = "before_release", summary = "security skill must report authz evidence", requirements = [{ label = "authz", detail = "tenant authorization result" }] }

[tool.asp-python.verification.skill_bindings]
security = { skill = "python-security-review", adapter = "bandit" }

[tool.asp-python.verification.skill_descriptors]
python-security-review = { task_kind = "security", adapter = "bandit", summary = "run bandit plus tenant authz probes", requirements = [{ label = "bandit", detail = "bandit report artifact" }] }
""",
    )

    config = read_asp_python_config(tmp_path)

    assert config is not None
    assert config.verification_policy.profile_hints[0].owner_path == "src/pkg/api.py"
    assert config.verification_policy.dependency_signals[0].package_name == "httpx"
    assert (
        config.verification_policy.skill_bindings[
            PythonVerificationTaskKind.SECURITY
        ].dispatch_hint
        == "python-security-review@bandit"
    )
    assert config.verification_policy.task_contracts[
        PythonVerificationTaskKind.SECURITY
    ].requirements[0] == PythonVerificationRequirement(
        "authz", "tenant authorization result"
    )
    assert config.verification_policy.skill_descriptors[
        "python-security-review@bandit"
    ].requirements[0] == PythonVerificationRequirement(
        "bandit", "bandit report artifact"
    )


def test_verification_skill_binding_renders_contract_reference(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    hint = (
        PythonVerificationProfileHint(
            "src/pkg/api.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        )
        .with_task_kinds((PythonVerificationTaskKind.SECURITY,))
        .with_task_contract(
            PythonVerificationTaskKind.SECURITY,
            PythonVerificationTaskContract(
                PythonVerificationPhase.BEFORE_RELEASE,
                "security review must include tenant authz evidence",
                (
                    PythonVerificationRequirement(
                        "tenant-authz",
                        "tenant authorization probe result",
                    ),
                ),
            ),
        )
        .with_rationale("this public API changes tenant authorization")
    )
    config = (
        default_python_harness_config()
        .with_verification_profile_hint(hint)
        .with_verification_skill_binding(
            PythonVerificationTaskKind.SECURITY,
            PythonVerificationSkillBinding(
                "python-security-review",
                adapter="bandit",
            ),
        )
        .with_verification_skill_descriptor(
            PythonVerificationSkillDescriptor(
                "python-security-review",
                PythonVerificationTaskKind.SECURITY,
                "run bandit and tenant authz probes",
                requirements=(
                    PythonVerificationRequirement(
                        "bandit",
                        "bandit report artifact",
                    ),
                ),
                adapter="bandit",
            )
        )
    )

    plan = plan_python_project_verification_with_config(tmp_path, config)
    compact = render_python_verification_plan(plan)
    contracts = render_python_verification_skill_contracts(plan)

    assert "skill=python-security-review@bandit" in compact
    assert "contract_ref=python-security-review@bandit" in compact
    assert "contract: security review must include tenant authz evidence" in contracts
    assert "descriptor: run bandit and tenant authz probes" in contracts
    assert "descriptor-required: bandit=bandit report artifact" in contracts


def test_agent_snapshot_includes_active_verification_tasks(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)
    config = default_python_harness_config().with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/api.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        )
        .with_task_kinds((PythonVerificationTaskKind.SECURITY,))
        .with_rationale("this public API needs a security review")
    )

    rendered = render_asp_python_agent_snapshot_with_config(
        tmp_path,
        config,
    )

    assert "[agent-snapshot] src python" in rendered
    assert "[tree] src python" in rendered
    assert "[verify-profile]" in rendered
    assert "[verify]" in rendered
    assert "src/pkg/api.py: security pending" in rendered


def _write_public_api_project(
    project_root: Path,
    *,
    dependencies: str = "",
    harness_config: str = "",
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

{harness_config}
""".lstrip(),
        encoding="utf-8",
    )
