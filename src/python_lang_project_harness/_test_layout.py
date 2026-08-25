"""Pytest layout rule pack aligned with the project harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._discovery import python_project_harness_scope
from ._model import PythonHarnessFinding, PythonRulePackDescriptor
from ._test_layout_bloat import bloated_unit_test_findings
from ._test_layout_catalog import TEST_LAYOUT_PACK_ID
from ._test_layout_entries import tests_root_entry_findings

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from python_lang_parser import PythonModuleReport

    from ._model import PythonProjectHarnessScope


@dataclass(frozen=True, slots=True)
class PythonTestLayoutRulePack:
    """Project-level pytest layout rules aligned with the Rust unit harness gate."""

    pack_id: str = TEST_LAYOUT_PACK_ID

    def descriptor(self) -> PythonRulePackDescriptor:
        """Return stable metadata for this rule pack."""

        return PythonRulePackDescriptor(
            id=self.pack_id,
            version="v1",
            domains=("pytest-layout", "unit-tests", "python"),
            default_mode="blocking",
        )

    def evaluate(self, report: PythonModuleReport) -> Iterable[PythonHarnessFinding]:
        """Module-level parser reports do not carry project layout authority."""

        return ()

    def evaluate_project(self, project_root: Path) -> Iterable[PythonHarnessFinding]:
        """Evaluate project-level pytest layout rules."""

        return self.evaluate_project_resolution(
            python_project_harness_scope(project_root)
        )

    def evaluate_project_resolution(
        self,
        scope: PythonProjectHarnessScope,
    ) -> Iterable[PythonHarnessFinding]:
        """Evaluate project-level pytest layout rules for monitored test roots."""

        return _test_layout_findings(scope, (), self.pack_id)

    def evaluate_project_modules(
        self,
        scope: PythonProjectHarnessScope,
        modules: Sequence[PythonModuleReport],
    ) -> Iterable[PythonHarnessFinding]:
        """Evaluate pytest layout rules using parser-owned module facts."""

        return _test_layout_findings(scope, modules, self.pack_id)


def _test_layout_findings(
    scope: PythonProjectHarnessScope,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[PythonHarnessFinding, ...]:
    findings: list[PythonHarnessFinding] = []
    for tests_dir in scope.test_paths:
        if not tests_dir.exists():
            continue
        findings.extend(tests_root_entry_findings(tests_dir, pack_id, modules))
    findings.extend(bloated_unit_test_findings(scope, modules, pack_id))
    return tuple(findings)
