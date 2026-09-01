"""Project policy advice for parser-backed verification profile setup."""

from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_parser import python_reasoning_tree_facts

from ._model import AspPythonConfig, AspPythonFinding
from ._project_config import read_asp_python_config
from ._project_policy_catalog import PY_PROJ_R011, project_policy_rule
from ._project_policy_pytest_gate import declares_python_harness_surface
from ._source import path_location, source_line
from .verification.facts import (
    is_test_path,
    parser_visible_owner_responsibilities,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonModuleReport, PythonProjectMetadata

    from ._model import PythonProjectHarnessScope


def project_verification_profile_findings(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return Agent advice when parser facts need a verification profile."""

    if not declares_python_harness_surface(metadata):
        return ()
    config = read_asp_python_config(scope.project_root)
    selected_config = config if config is not None else AspPythonConfig()
    if selected_config.verification_policy.profile_hints:
        return ()

    owner_count = _verification_owner_count(scope, metadata, modules, selected_config)
    if owner_count == 0:
        return ()

    rule = project_policy_rule(PY_PROJ_R011)
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=(
                f"{metadata.pyproject_path.name} has {owner_count} parser-visible "
                "verification owner candidates but no profile hints."
            ),
            location=path_location(metadata.pyproject_path),
            requirement=rule.requirement,
            source_line=source_line(str(metadata.pyproject_path), 1),
            label="configure parser-backed verification profile hints",
            labels=dict(rule.labels),
        ),
    )


def _verification_owner_count(
    scope: PythonProjectHarnessScope,
    metadata: PythonProjectMetadata,
    modules: Sequence[PythonModuleReport],
    config: AspPythonConfig,
) -> int:
    facts = python_reasoning_tree_facts(
        modules,
        import_roots=scope.source_paths or scope.monitored_paths,
        project_root=scope.project_root,
        project_metadata=metadata,
    )
    owners = parser_visible_owner_responsibilities(
        facts,
        project_root=scope.project_root,
        dependency_signals=config.verification_policy.dependency_signals,
    )
    return sum(1 for path in owners if not is_test_path(path))
