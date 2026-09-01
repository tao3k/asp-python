"""Report bundle writer for Python verification plans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .model import (
    PythonVerificationPlan,
    PythonVerificationReportObligation,
    PythonVerificationReportPersistence,
)
from .render import (
    render_python_verification_performance_index_json,
    render_python_verification_plan_json,
    render_python_verification_task_index_json,
)


@dataclass(frozen=True, slots=True)
class PythonVerificationReportArtifact:
    """Manifest entry for one persistable verification artifact."""

    key: str
    renderer: str
    artifact: str
    persistence: PythonVerificationReportPersistence
    task_kinds: tuple[str, ...]

    @classmethod
    def from_obligation(
        cls,
        obligation: PythonVerificationReportObligation,
    ) -> PythonVerificationReportArtifact:
        """Build one artifact manifest entry from a plan obligation."""

        return cls(
            key=obligation.key,
            renderer=obligation.renderer,
            artifact=obligation.artifact,
            persistence=obligation.persistence,
            task_kinds=tuple(kind.value for kind in obligation.task_kinds),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "key": self.key,
            "renderer": self.renderer,
            "artifact": self.artifact,
            "persistence": self.persistence.value,
            "task_kinds": list(self.task_kinds),
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationReportBundle:
    """Small manifest for modular verification report artifacts."""

    project_root: Path
    artifacts: tuple[PythonVerificationReportArtifact, ...]

    def artifact(self, key: str) -> PythonVerificationReportArtifact | None:
        """Return one artifact by key."""

        return next(
            (artifact for artifact in self.artifacts if artifact.key == key), None
        )

    def source_baseline_artifacts(
        self,
    ) -> tuple[PythonVerificationReportArtifact, ...]:
        """Return artifacts intended for source-controlled baselines."""

        return tuple(
            artifact
            for artifact in self.artifacts
            if artifact.persistence
            == PythonVerificationReportPersistence.SOURCE_BASELINE
        )

    def runtime_cache_artifacts(
        self,
    ) -> tuple[PythonVerificationReportArtifact, ...]:
        """Return artifacts intended for runtime cache storage."""

        return tuple(
            artifact
            for artifact in self.artifacts
            if artifact.persistence == PythonVerificationReportPersistence.RUNTIME_CACHE
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "project_root": str(self.project_root),
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationReportWriteConfig:
    """Filesystem roots for modular verification report persistence."""

    source_baseline_dir: Path
    runtime_cache_dir: Path


@dataclass(frozen=True, slots=True)
class PythonVerificationReportWriteReceipt:
    """Paths written by `write_python_verification_reports`."""

    manifest_paths: tuple[Path, ...]
    artifact_paths: tuple[Path, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "manifest_paths": [str(path) for path in self.manifest_paths],
            "artifact_paths": [str(path) for path in self.artifact_paths],
        }


def build_python_verification_report_bundle(
    plan: PythonVerificationPlan,
) -> PythonVerificationReportBundle:
    """Build a report artifact manifest for active verification tasks."""

    return PythonVerificationReportBundle(
        project_root=plan.project_root,
        artifacts=tuple(
            PythonVerificationReportArtifact.from_obligation(obligation)
            for obligation in plan.report_obligations
        ),
    )


def render_python_verification_report_bundle_json(
    plan: PythonVerificationPlan,
) -> str:
    """Render the report bundle manifest as JSON."""

    return json.dumps(
        build_python_verification_report_bundle(plan).to_dict(),
        separators=(",", ":"),
        sort_keys=True,
    )


def render_python_verification_report_artifact_json(
    plan: PythonVerificationPlan,
    key: str,
) -> str | None:
    """Render one report artifact payload by key."""

    match key:
        case "verification_plan_json":
            return render_python_verification_plan_json(plan)
        case "task_index_json":
            return render_python_verification_task_index_json(plan)
        case "performance_index_json":
            return render_python_verification_performance_index_json(plan)
        case _:
            return None


def write_python_verification_reports(
    plan: PythonVerificationPlan,
    config: PythonVerificationReportWriteConfig,
) -> PythonVerificationReportWriteReceipt:
    """Write modular verification artifacts and manifests."""

    bundle = build_python_verification_report_bundle(plan)
    source_manifest_path = (
        config.source_baseline_dir / "verification_report_manifest.json"
    )
    runtime_manifest_path = (
        config.runtime_cache_dir / "verification_report_manifest.json"
    )
    artifact_paths: list[Path] = []
    _write_manifest(
        source_manifest_path,
        project_root=bundle.project_root,
        artifacts=bundle.source_baseline_artifacts(),
    )
    _write_manifest(
        runtime_manifest_path,
        project_root=bundle.project_root,
        artifacts=bundle.artifacts,
    )
    for artifact in bundle.artifacts:
        payload = render_python_verification_report_artifact_json(plan, artifact.key)
        if payload is None:
            continue
        target_dir = (
            config.source_baseline_dir
            if artifact.persistence
            == PythonVerificationReportPersistence.SOURCE_BASELINE
            else config.runtime_cache_dir
        )
        target_path = target_dir / artifact.artifact
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(payload + "\n", encoding="utf-8")
        artifact_paths.append(target_path)
    return PythonVerificationReportWriteReceipt(
        manifest_paths=(source_manifest_path, runtime_manifest_path),
        artifact_paths=tuple(artifact_paths),
    )


def _write_manifest(
    path: Path,
    *,
    project_root: Path,
    artifacts: tuple[PythonVerificationReportArtifact, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {
            "project_root": str(project_root),
            "artifacts": [artifact.to_dict() for artifact in artifacts],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    path.write_text(payload + "\n", encoding="utf-8")
