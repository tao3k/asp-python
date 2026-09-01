"""Modern Python project-shape rule pack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._model import AspPythonFinding, PythonRulePackDescriptor
from ._project_metadata import read_python_project_metadata
from ._project_policy_catalog import PROJECT_POLICY_PACK_ID
from ._project_policy_imports import project_import_name_findings
from ._project_policy_layout import project_layout_findings
from ._project_policy_metadata import project_metadata_findings
from ._project_policy_pytest_gate import project_pytest_gate_findings
from ._project_policy_typed import typed_package_findings
from ._project_policy_verification import project_verification_profile_findings

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from python_lang_parser import PythonModuleReport

    from ._model import PythonProjectHarnessScope


@dataclass(frozen=True, slots=True)
class PythonProjectPolicyRulePack:
    """Rules for modern Python project metadata and package shape."""

    pack_id: str = PROJECT_POLICY_PACK_ID

    def descriptor(self) -> PythonRulePackDescriptor:
        """Return stable metadata for this rule pack."""

        return PythonRulePackDescriptor(
            id=self.pack_id,
            version="v1",
            domains=("project-policy", "packaging", "python"),
            default_mode="blocking",
        )

    def evaluate(self, report: PythonModuleReport) -> Iterable[AspPythonFinding]:
        """Evaluate per-module rules."""

        return ()

    def evaluate_project_modules(
        self,
        scope: PythonProjectHarnessScope,
        modules: Sequence[PythonModuleReport],
    ) -> Iterable[AspPythonFinding]:
        """Evaluate project-shape rules over a parsed project."""

        metadata = scope.project_metadata or read_python_project_metadata(
            scope.project_root
        )
        if metadata is None:
            return ()

        findings: list[AspPythonFinding] = []
        findings.extend(project_metadata_findings(metadata, self.pack_id))
        findings.extend(project_layout_findings(scope, metadata, self.pack_id))
        findings.extend(
            project_import_name_findings(scope, metadata, modules, self.pack_id)
        )
        findings.extend(project_pytest_gate_findings(metadata, modules, self.pack_id))
        findings.extend(
            project_verification_profile_findings(
                scope,
                metadata,
                modules,
                self.pack_id,
            )
        )
        findings.extend(typed_package_findings(metadata, modules, self.pack_id))
        return tuple(findings)
