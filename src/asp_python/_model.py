"""Data model for embedded Python language harness reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import TYPE_CHECKING, Protocol

from ._constants import (
    DEFAULT_BLOCKING_SEVERITIES,
    IGNORED_DIR_NAMES,
    INCLUDE_HIDDEN_DIR_NAMES,
)
from .verification.model import (
    PythonVerificationDependencySignal,
    PythonVerificationPolicy,
    PythonVerificationProfileHint,
    PythonVerificationReceipt,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTaskContract,
    PythonVerificationTaskKind,
    PythonVerificationWaiver,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from python_lang_parser import (
        PythonDiagnosticSeverity,
        PythonModuleReport,
        PythonProjectMetadata,
        SourceLocation,
    )


@dataclass(frozen=True, slots=True)
class PythonRulePackDescriptor:
    """Stable metadata for one Python language harness rule pack."""

    id: str
    version: str
    domains: tuple[str, ...]
    default_mode: str = "deterministic"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        payload = asdict(self)
        payload["domains"] = list(self.domains)
        return payload


@dataclass(frozen=True, slots=True)
class AspPythonRule:
    """Compact metadata for one deterministic harness rule."""

    rule_id: str
    pack_id: str
    severity: PythonDiagnosticSeverity
    title: str
    requirement: str
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True, slots=True)
class AspPythonFinding:
    """One deterministic Python harness finding."""

    rule_id: str
    pack_id: str
    severity: PythonDiagnosticSeverity
    title: str
    summary: str
    location: SourceLocation
    requirement: str
    source_line: str | None = None
    label: str = "repair Python syntax near this token"
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True, slots=True)
class PythonProjectHarnessScope:
    """Concrete project paths monitored by an embedded Python harness run."""

    project_root: Path
    project_metadata: PythonProjectMetadata | None = None
    project_paths: tuple[Path, ...] = ()
    source_paths: tuple[Path, ...] = ()
    test_paths: tuple[Path, ...] = ()
    extra_paths: tuple[Path, ...] = ()
    include_tests: bool = True
    fallback_paths: tuple[Path, ...] = ()

    @property
    def monitored_paths(self) -> tuple[Path, ...]:
        """Return the concrete roots scanned by the parser and rule packs."""

        selected = self.project_paths
        if selected:
            return _dedupe_paths((*selected, *self.extra_paths))
        selected = (
            (*self.source_paths, *self.test_paths, *self.extra_paths)
            if self.include_tests
            else (*self.source_paths, *self.extra_paths)
        )
        if selected:
            return _dedupe_paths(selected)
        return self.fallback_paths

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "project_root": str(self.project_root),
            "project_metadata": (
                None
                if self.project_metadata is None
                else self.project_metadata.to_dict()
            ),
            "project_paths": [str(path) for path in self.project_paths],
            "source_paths": [str(path) for path in self.source_paths],
            "test_paths": [str(path) for path in self.test_paths],
            "extra_paths": [str(path) for path in self.extra_paths],
            "include_tests": self.include_tests,
            "monitored_paths": [str(path) for path in self.monitored_paths],
        }


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return tuple(deduped)


class PythonLangRulePack(Protocol):
    """Protocol for Python language harness rule packs."""

    pack_id: str

    def descriptor(self) -> PythonRulePackDescriptor:
        """Return stable metadata for this rule pack."""

    def evaluate(self, report: PythonModuleReport) -> Iterable[AspPythonFinding]:
        """Evaluate one parsed module report."""


@dataclass(frozen=True, slots=True)
class AspPythonConfig:
    """Configuration for an embedded Python language harness run."""

    ignored_dir_names: frozenset[str] = IGNORED_DIR_NAMES
    include_hidden_dir_names: frozenset[str] = INCLUDE_HIDDEN_DIR_NAMES
    blocking_severities: frozenset[PythonDiagnosticSeverity] = (
        DEFAULT_BLOCKING_SEVERITIES
    )
    include_tests: bool = True
    source_dir_names: tuple[str, ...] = ("src",)
    test_dir_names: tuple[str, ...] = ("tests",)
    extra_path_names: tuple[str, ...] = ()
    disabled_rule_ids: frozenset[str] = frozenset()
    blocking_rule_ids: frozenset[str] = frozenset()
    verification_policy: PythonVerificationPolicy = field(
        default_factory=PythonVerificationPolicy
    )
    rule_packs: tuple[PythonLangRulePack, ...] | None = None

    def with_verification_policy(
        self,
        policy: PythonVerificationPolicy,
    ) -> AspPythonConfig:
        """Return a config with an explicit verification policy."""

        return replace(self, verification_policy=policy)

    def with_verification_profile_hint(
        self,
        hint: PythonVerificationProfileHint,
    ) -> AspPythonConfig:
        """Return a config with one verification profile hint appended."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_profile_hint(hint),
        )

    def with_verification_dependency_signal(
        self,
        signal: PythonVerificationDependencySignal,
    ) -> AspPythonConfig:
        """Return a config with one dependency-to-responsibility signal."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_dependency_signal(signal),
        )

    def with_verification_receipt(
        self,
        receipt: PythonVerificationReceipt,
    ) -> AspPythonConfig:
        """Return a config with one verification receipt appended."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_receipt(receipt),
        )

    def with_verification_waiver(
        self,
        waiver: PythonVerificationWaiver,
    ) -> AspPythonConfig:
        """Return a config with one verification waiver appended."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_waiver(waiver),
        )

    def with_verification_task_contract(
        self,
        kind: PythonVerificationTaskKind,
        contract: PythonVerificationTaskContract,
    ) -> AspPythonConfig:
        """Return a config with one verification task contract override."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_task_contract(
                kind,
                contract,
            ),
        )

    def with_verification_skill_binding(
        self,
        kind: PythonVerificationTaskKind,
        binding: PythonVerificationSkillBinding,
    ) -> AspPythonConfig:
        """Return a config with one verification skill binding."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_skill_binding(
                kind,
                binding,
            ),
        )

    def with_verification_skill_descriptor(
        self,
        descriptor: PythonVerificationSkillDescriptor,
    ) -> AspPythonConfig:
        """Return a config with one verification skill descriptor."""

        return replace(
            self,
            verification_policy=self.verification_policy.with_skill_descriptor(
                descriptor
            ),
        )


@dataclass(frozen=True, slots=True)
class AspPythonReport:
    """Aggregated Python language harness report."""

    modules: tuple[PythonModuleReport, ...]
    findings: tuple[AspPythonFinding, ...]
    root_paths: tuple[str, ...]
    blocking_severities: frozenset[PythonDiagnosticSeverity] = (
        DEFAULT_BLOCKING_SEVERITIES
    )
    project_resolution: PythonProjectHarnessScope | None = None
    disabled_rule_ids: frozenset[str] = frozenset()
    blocking_rule_ids: frozenset[str] = frozenset()

    @property
    def parsed_count(self) -> int:
        """Return the number of parser-clean modules."""

        return sum(1 for module in self.modules if module.is_valid)

    @property
    def file_count(self) -> int:
        """Return the number of modules included in the report."""

        return len(self.modules)

    @property
    def is_clean(self) -> bool:
        """Return whether the report contains no configured-blocking findings."""

        return not self.blocking_findings()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "root_paths": list(self.root_paths),
            "project_resolution": (
                None
                if self.project_resolution is None
                else self.project_resolution.to_dict()
            ),
            "file_count": self.file_count,
            "parsed_count": self.parsed_count,
            "is_clean": self.is_clean,
            "blocking_severities": [
                severity.value for severity in sorted(self.blocking_severities)
            ],
            "disabled_rule_ids": sorted(self.disabled_rule_ids),
            "blocking_rule_ids": sorted(self.blocking_rule_ids),
            "findings": [finding.to_dict() for finding in self.findings],
            "modules": [module.to_dict() for module in self.modules],
        }

    def blocking_findings(
        self,
        *,
        severities: frozenset[PythonDiagnosticSeverity] | None = None,
    ) -> tuple[AspPythonFinding, ...]:
        """Return findings that should block a pytest assertion."""

        blocking_severities = (
            self.blocking_severities if severities is None else severities
        )
        return tuple(
            finding
            for finding in self.findings
            if finding.rule_id in self.blocking_rule_ids
            or finding.severity in blocking_severities
        )

    def advisory_findings(
        self,
        *,
        severities: frozenset[PythonDiagnosticSeverity] | None = None,
    ) -> tuple[AspPythonFinding, ...]:
        """Return non-blocking advisory findings for agent-guided repair."""

        if severities is None:
            from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

            selected_severities = frozenset({PythonDiagnosticSeverity.INFO})
        else:
            selected_severities = severities
        return tuple(
            finding
            for finding in self.findings
            if finding.severity in selected_severities
        )

    def assert_clean(
        self,
        *,
        severities: frozenset[PythonDiagnosticSeverity] | None = None,
        include_advice: bool = True,
    ) -> None:
        """Raise `AssertionError` when blocking findings are present."""

        if self.blocking_findings(severities=severities):
            from ._render import render_python_lang_harness

            raise AssertionError(
                render_python_lang_harness(
                    self,
                    severities=severities,
                    include_advice=include_advice,
                )
            )
