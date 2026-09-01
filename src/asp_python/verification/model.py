"""Library-first verification planning model for Python project harnesses."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path


class PythonOwnerResponsibility(StrEnum):
    """Parser-backed responsibilities that may require external verification."""

    PUBLIC_API = "public_api"
    CLI = "cli"
    PYTEST_GATE = "pytest_gate"
    NETWORK = "network"
    PERSISTENCE = "persistence"
    PERFORMANCE = "performance"


class PythonVerificationTaskKind(StrEnum):
    """External task classes planned by the harness but executed by skills."""

    PERFORMANCE = "performance"
    SECURITY = "security"
    STRESS = "stress"
    CHAOS = "chaos"
    REGRESSION = "regression"
    RESPONSIBILITY_REVIEW = "responsibility_review"


class PythonVerificationPhase(StrEnum):
    """Lifecycle phase for one verification obligation."""

    BEFORE_VERIFICATION = "before_verification"
    BEFORE_RELEASE = "before_release"


class PythonVerificationTaskState(StrEnum):
    """Current state of one verification task."""

    PENDING = "pending"
    SATISFIED = "satisfied"
    WAIVED = "waived"


class PythonVerificationReportPersistence(StrEnum):
    """Persistence class for generated verification report artifacts."""

    SOURCE_BASELINE = "source_baseline"
    RUNTIME_CACHE = "runtime_cache"


@dataclass(frozen=True, slots=True)
class PythonVerificationEvidence:
    """One compact evidence key/value attached to a task or profile candidate."""

    label: str
    value: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible representation."""

        return {"label": self.label, "value": self.value}


@dataclass(frozen=True, slots=True)
class PythonVerificationRequirement:
    """One requirement line for an external verification skill contract."""

    label: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible representation."""

        return {"label": self.label, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class PythonVerificationSkillBinding:
    """Low-token bridge from a verification task kind to an Agent skill."""

    skill: str
    adapter: str | None = None

    def with_adapter(self, adapter: str) -> PythonVerificationSkillBinding:
        """Return a binding with a concrete execution adapter."""

        return replace(self, adapter=adapter)

    @property
    def dispatch_hint(self) -> str:
        """Return a compact `skill@adapter` dispatch hint."""

        if self.adapter is None:
            return self.skill
        return f"{self.skill}@{self.adapter}"

    def to_dict(self) -> dict[str, str | None]:
        """Return a JSON-compatible representation."""

        return {
            "skill": self.skill,
            "adapter": self.adapter,
            "dispatch_hint": self.dispatch_hint,
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationSkillDescriptor:
    """Typed execution contract for a verification skill binding."""

    key: str
    task_kind: PythonVerificationTaskKind
    summary: str
    requirements: tuple[PythonVerificationRequirement, ...] = ()
    adapter: str | None = None

    @classmethod
    def pytest_regression(cls) -> PythonVerificationSkillDescriptor:
        """Return a standard pytest regression skill descriptor."""

        return cls(
            key="python-verification-regression",
            task_kind=PythonVerificationTaskKind.REGRESSION,
            adapter="pytest",
            summary="run the parser-owned pytest regression contract",
            requirements=(
                PythonVerificationRequirement(
                    "pytest",
                    "capture command, exit status, and failing node ids",
                ),
            ),
        )

    @classmethod
    def performance(cls) -> PythonVerificationSkillDescriptor:
        """Return a standard Python performance skill descriptor."""

        return cls(
            key="python-verification-performance",
            task_kind=PythonVerificationTaskKind.PERFORMANCE,
            adapter="pytest-benchmark",
            summary="measure performance-sensitive Python owner behavior",
            requirements=(
                PythonVerificationRequirement(
                    "benchmark",
                    "record command, sample size, and baseline comparison",
                ),
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "key": self.key,
            "compact_label": self.compact_label,
            "task_kind": self.task_kind.value,
            "summary": self.summary,
            "adapter": self.adapter,
            "requirements": [item.to_dict() for item in self.requirements],
        }

    @property
    def compact_label(self) -> str:
        """Return a compact descriptor label for task contract references."""

        if self.adapter is None:
            return self.key
        return f"{self.key}@{self.adapter}"


@dataclass(frozen=True, slots=True)
class PythonVerificationTaskContract:
    """Contract text attached to one task kind."""

    phase: PythonVerificationPhase
    summary: str
    requirements: tuple[PythonVerificationRequirement, ...] = ()

    @classmethod
    def default_for(
        cls,
        kind: PythonVerificationTaskKind,
    ) -> PythonVerificationTaskContract:
        """Return the default task contract for one task kind."""

        if kind == PythonVerificationTaskKind.RESPONSIBILITY_REVIEW:
            return cls(
                phase=PythonVerificationPhase.BEFORE_VERIFICATION,
                summary="update the verification profile to match parser facts, or attach a complete waiver",
            )
        return cls(
            phase=PythonVerificationPhase.BEFORE_RELEASE,
            summary=f"run {kind.value} verification for this parser-owned owner",
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "phase": self.phase.value,
            "summary": self.summary,
            "requirements": [item.to_dict() for item in self.requirements],
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationProfileHint:
    """Config hint that maps one owner path to verification responsibilities."""

    owner_path: str
    responsibilities: tuple[PythonOwnerResponsibility, ...]
    task_kinds: tuple[PythonVerificationTaskKind, ...] = ()
    verification_tasks_enabled: bool = True
    rationale: str = ""
    task_contracts: dict[
        PythonVerificationTaskKind,
        PythonVerificationTaskContract,
    ] = field(default_factory=dict)

    def with_task_kinds(
        self,
        task_kinds: tuple[PythonVerificationTaskKind, ...],
    ) -> PythonVerificationProfileHint:
        """Return a hint with owner-local task kinds."""

        return replace(self, task_kinds=tuple(task_kinds))

    def without_verification_tasks(self) -> PythonVerificationProfileHint:
        """Return a hint that intentionally suppresses owner-local tasks."""

        return replace(self, verification_tasks_enabled=False, task_kinds=())

    def with_rationale(self, rationale: str) -> PythonVerificationProfileHint:
        """Return a hint with compact rationale text."""

        return replace(self, rationale=rationale)

    def with_task_contract(
        self,
        kind: PythonVerificationTaskKind,
        contract: PythonVerificationTaskContract,
    ) -> PythonVerificationProfileHint:
        """Return a hint with an owner-local task contract override."""

        return replace(
            self,
            task_contracts={**self.task_contracts, kind: contract},
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "owner_path": self.owner_path,
            "responsibilities": [item.value for item in self.responsibilities],
            "task_kinds": [item.value for item in self.task_kinds],
            "verification_tasks_enabled": self.verification_tasks_enabled,
            "rationale": self.rationale,
            "task_contracts": {
                key.value: value.to_dict()
                for key, value in sorted(
                    self.task_contracts.items(),
                    key=lambda item: item[0].value,
                )
            },
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationDependencySignal:
    """Config mapping from dependency facts to owner responsibilities."""

    package_name: str
    responsibilities: tuple[PythonOwnerResponsibility, ...]
    task_kinds: tuple[PythonVerificationTaskKind, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "package_name": self.package_name,
            "responsibilities": [item.value for item in self.responsibilities],
            "task_kinds": [item.value for item in self.task_kinds],
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationReceipt:
    """Evidence receipt that satisfies one planned verification task."""

    task_fingerprint: str
    summary: str = ""
    evidence: tuple[PythonVerificationEvidence, ...] = ()

    def with_evidence(
        self,
        evidence: tuple[PythonVerificationEvidence, ...],
    ) -> PythonVerificationReceipt:
        """Return a receipt with evidence attached."""

        return replace(self, evidence=tuple(evidence))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "task_fingerprint": self.task_fingerprint,
            "summary": self.summary,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationWaiver:
    """Explicit waiver for one planned verification task."""

    task_fingerprint: str
    rationale: str

    @property
    def is_complete(self) -> bool:
        """Return whether the waiver has enough rationale to suppress a task."""

        return bool(self.rationale.strip())

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "task_fingerprint": self.task_fingerprint,
            "rationale": self.rationale,
            "is_complete": self.is_complete,
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationTask:
    """One external verification obligation planned by the harness."""

    owner_path: str
    owner_namespace: tuple[str, ...]
    responsibilities: tuple[PythonOwnerResponsibility, ...]
    kind: PythonVerificationTaskKind
    state: PythonVerificationTaskState
    phase: PythonVerificationPhase
    fingerprint: str
    why: str
    contract: PythonVerificationTaskContract
    evidence: tuple[PythonVerificationEvidence, ...] = ()
    receipt: PythonVerificationReceipt | None = None
    waiver: PythonVerificationWaiver | None = None
    skill_binding: PythonVerificationSkillBinding | None = None
    skill_descriptor: PythonVerificationSkillDescriptor | None = None

    @property
    def is_active(self) -> bool:
        """Return whether the task still needs external action."""

        return self.state == PythonVerificationTaskState.PENDING

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "owner_path": self.owner_path,
            "owner_namespace": list(self.owner_namespace),
            "responsibilities": [item.value for item in self.responsibilities],
            "kind": self.kind.value,
            "state": self.state.value,
            "phase": self.phase.value,
            "fingerprint": self.fingerprint,
            "why": self.why,
            "contract": self.contract.to_dict(),
            "evidence": [item.to_dict() for item in self.evidence],
            "receipt": None if self.receipt is None else self.receipt.to_dict(),
            "waiver": None if self.waiver is None else self.waiver.to_dict(),
            "skill_binding": (
                None if self.skill_binding is None else self.skill_binding.to_dict()
            ),
            "skill_descriptor": (
                None
                if self.skill_descriptor is None
                else self.skill_descriptor.to_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationReportObligation:
    """One report artifact required by an active verification plan."""

    key: str
    renderer: str
    artifact: str
    task_kinds: tuple[PythonVerificationTaskKind, ...]
    persistence: PythonVerificationReportPersistence

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "key": self.key,
            "renderer": self.renderer,
            "artifact": self.artifact,
            "task_kinds": [item.value for item in self.task_kinds],
            "persistence": self.persistence.value,
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationPolicy:
    """Configurable verification policy attached to a harness config."""

    profile_hints: tuple[PythonVerificationProfileHint, ...] = ()
    dependency_signals: tuple[PythonVerificationDependencySignal, ...] = ()
    receipts: tuple[PythonVerificationReceipt, ...] = ()
    waivers: tuple[PythonVerificationWaiver, ...] = ()
    responsibility_task_kinds: dict[
        PythonOwnerResponsibility,
        tuple[PythonVerificationTaskKind, ...],
    ] = field(default_factory=dict)
    task_contracts: dict[
        PythonVerificationTaskKind,
        PythonVerificationTaskContract,
    ] = field(default_factory=dict)
    skill_bindings: dict[
        PythonVerificationTaskKind,
        PythonVerificationSkillBinding,
    ] = field(default_factory=dict)
    skill_descriptors: dict[
        str,
        PythonVerificationSkillDescriptor,
    ] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """Return whether the policy has no configured verification behavior."""

        return not (
            self.profile_hints
            or self.dependency_signals
            or self.receipts
            or self.waivers
            or self.responsibility_task_kinds
            or self.task_contracts
            or self.skill_bindings
            or self.skill_descriptors
        )

    def task_kinds_for_responsibilities(
        self,
        responsibilities: tuple[PythonOwnerResponsibility, ...],
    ) -> tuple[PythonVerificationTaskKind, ...]:
        """Return configured task kinds for owner responsibilities."""

        task_kinds: list[PythonVerificationTaskKind] = []
        seen: set[PythonVerificationTaskKind] = set()
        for responsibility in responsibilities:
            for kind in self.responsibility_task_kinds.get(
                responsibility,
                _default_task_kinds_for_responsibility(responsibility),
            ):
                if kind in seen:
                    continue
                seen.add(kind)
                task_kinds.append(kind)
        return tuple(task_kinds)

    def with_profile_hint(
        self,
        hint: PythonVerificationProfileHint,
    ) -> PythonVerificationPolicy:
        """Return a policy with one profile hint appended."""

        return replace(self, profile_hints=(*self.profile_hints, hint))

    def with_dependency_signal(
        self,
        signal: PythonVerificationDependencySignal,
    ) -> PythonVerificationPolicy:
        """Return a policy with one dependency signal appended."""

        return replace(self, dependency_signals=(*self.dependency_signals, signal))

    def with_receipt(
        self,
        receipt: PythonVerificationReceipt,
    ) -> PythonVerificationPolicy:
        """Return a policy with one verification receipt appended."""

        return replace(self, receipts=(*self.receipts, receipt))

    def with_waiver(
        self,
        waiver: PythonVerificationWaiver,
    ) -> PythonVerificationPolicy:
        """Return a policy with one verification waiver appended."""

        return replace(self, waivers=(*self.waivers, waiver))

    def with_task_contract(
        self,
        kind: PythonVerificationTaskKind,
        contract: PythonVerificationTaskContract,
    ) -> PythonVerificationPolicy:
        """Return a policy with one task-kind contract override."""

        return replace(
            self,
            task_contracts={**self.task_contracts, kind: contract},
        )

    def with_skill_binding(
        self,
        kind: PythonVerificationTaskKind,
        binding: PythonVerificationSkillBinding,
    ) -> PythonVerificationPolicy:
        """Return a policy with one task-kind skill binding."""

        return replace(
            self,
            skill_bindings={**self.skill_bindings, kind: binding},
        )

    def with_skill_descriptor(
        self,
        descriptor: PythonVerificationSkillDescriptor,
    ) -> PythonVerificationPolicy:
        """Return a policy with one compact skill descriptor."""

        return replace(
            self,
            skill_descriptors={
                **self.skill_descriptors,
                descriptor.compact_label: descriptor,
            },
        )

    def with_responsibility_task_kinds(
        self,
        responsibility: PythonOwnerResponsibility,
        task_kinds: tuple[PythonVerificationTaskKind, ...],
    ) -> PythonVerificationPolicy:
        """Return a policy with one responsibility task-kind mapping."""

        return replace(
            self,
            responsibility_task_kinds={
                **self.responsibility_task_kinds,
                responsibility: tuple(task_kinds),
            },
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "profile_hints": [item.to_dict() for item in self.profile_hints],
            "dependency_signals": [item.to_dict() for item in self.dependency_signals],
            "receipts": [item.to_dict() for item in self.receipts],
            "waivers": [item.to_dict() for item in self.waivers],
            "responsibility_task_kinds": {
                key.value: [item.value for item in value]
                for key, value in sorted(
                    self.responsibility_task_kinds.items(),
                    key=lambda item: item[0].value,
                )
            },
            "task_contracts": {
                key.value: value.to_dict()
                for key, value in sorted(
                    self.task_contracts.items(),
                    key=lambda item: item[0].value,
                )
            },
            "skill_bindings": {
                key.value: value.to_dict()
                for key, value in sorted(
                    self.skill_bindings.items(),
                    key=lambda item: item[0].value,
                )
            },
            "skill_descriptors": {
                key: value.to_dict()
                for key, value in sorted(self.skill_descriptors.items())
            },
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationPlan:
    """Complete parser-backed verification plan for one project."""

    project_root: Path
    tasks: tuple[PythonVerificationTask, ...]
    report_obligations: tuple[PythonVerificationReportObligation, ...]

    @property
    def active_tasks(self) -> tuple[PythonVerificationTask, ...]:
        """Return pending tasks that still require external action."""

        return tuple(task for task in self.tasks if task.is_active)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "project_root": str(self.project_root),
            "tasks": [item.to_dict() for item in self.tasks],
            "active_tasks": [item.fingerprint for item in self.active_tasks],
            "report_obligations": [item.to_dict() for item in self.report_obligations],
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationProfileCandidate:
    """One parser-suggested verification profile candidate."""

    owner_path: str
    owner_namespace: tuple[str, ...]
    responsibilities: tuple[PythonOwnerResponsibility, ...]
    state: str
    configured_responsibilities: tuple[PythonOwnerResponsibility, ...] = ()
    evidence: tuple[PythonVerificationEvidence, ...] = ()
    task_kinds: tuple[PythonVerificationTaskKind, ...] = ()

    def to_profile_hint(self) -> PythonVerificationProfileHint:
        """Return the config hint represented by this parser candidate."""

        return PythonVerificationProfileHint(
            owner_path=self.owner_path,
            responsibilities=self.responsibilities,
            task_kinds=self.task_kinds,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "owner_path": self.owner_path,
            "owner_namespace": list(self.owner_namespace),
            "responsibilities": [item.value for item in self.responsibilities],
            "state": self.state,
            "configured_responsibilities": [
                item.value for item in self.configured_responsibilities
            ],
            "evidence": [item.to_dict() for item in self.evidence],
            "task_kinds": [item.value for item in self.task_kinds],
        }


@dataclass(frozen=True, slots=True)
class PythonVerificationProfileIndex:
    """Low-token profile advice built from parser project facts."""

    project_root: Path
    candidates: tuple[PythonVerificationProfileCandidate, ...]
    configured_profile_hint_count: int = 0

    def active_candidates(self) -> tuple[PythonVerificationProfileCandidate, ...]:
        """Return candidates that still need Agent configuration attention."""

        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.state != "configured"
        )

    def is_clear(self) -> bool:
        """Return whether all parser-suggested profile candidates are configured."""

        return not self.active_candidates()

    def needs_profile_configuration(self) -> bool:
        """Return whether parser facts found owners before any profile was configured."""

        return self.configured_profile_hint_count == 0 and bool(
            self.active_candidates()
        )

    def active_profile_hints(self) -> tuple[PythonVerificationProfileHint, ...]:
        """Return config-ready hints for candidates still needing attention."""

        return tuple(
            candidate.to_profile_hint() for candidate in self.active_candidates()
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "project_root": str(self.project_root),
            "candidates": [item.to_dict() for item in self.candidates],
            "configured_profile_hint_count": self.configured_profile_hint_count,
            "needs_profile_configuration": self.needs_profile_configuration(),
            "active_profile_hints": [
                item.to_dict() for item in self.active_profile_hints()
            ],
        }


def _default_task_kinds_for_responsibility(
    responsibility: PythonOwnerResponsibility,
) -> tuple[PythonVerificationTaskKind, ...]:
    match responsibility:
        case PythonOwnerResponsibility.PUBLIC_API:
            return (PythonVerificationTaskKind.REGRESSION,)
        case PythonOwnerResponsibility.CLI:
            return (PythonVerificationTaskKind.REGRESSION,)
        case PythonOwnerResponsibility.PYTEST_GATE:
            return (PythonVerificationTaskKind.REGRESSION,)
        case PythonOwnerResponsibility.NETWORK:
            return (PythonVerificationTaskKind.STRESS,)
        case PythonOwnerResponsibility.PERSISTENCE:
            return (PythonVerificationTaskKind.REGRESSION,)
        case PythonOwnerResponsibility.PERFORMANCE:
            return (PythonVerificationTaskKind.PERFORMANCE,)
