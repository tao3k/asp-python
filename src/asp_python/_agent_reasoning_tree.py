"""Agent-facing reasoning-tree advice backed by parser-owned package facts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser import python_reasoning_tree_facts

from ._agent_policy_catalog import PY_AGENT_R007, PY_AGENT_R008, agent_policy_rule
from ._model import AspPythonFinding
from ._source import path_location

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import (
        PythonModuleReport,
        PythonReasoningTreeBranch,
        PythonReasoningTreeFacts,
        PythonReasoningTreeNode,
    )

    from ._model import PythonProjectHarnessScope

_MAX_AGENT_BRANCH_CHILDREN = 6
_MIN_AGENT_BRANCH_PUBLIC_CHILDREN = 4
_MIN_AGENT_BRANCH_EFFECTIVE_LINES = 220


def agent_reasoning_tree_findings(
    scope: PythonProjectHarnessScope,
    modules: Sequence[PythonModuleReport],
    pack_id: str,
) -> tuple[AspPythonFinding, ...]:
    """Return agent advice for package-tree navigation gaps."""

    facts = python_reasoning_tree_facts(
        modules,
        import_roots=_reasoning_tree_import_roots(scope),
        project_root=scope.project_root,
        project_metadata=scope.project_metadata,
    )
    modules_by_path = {
        module.path: module for module in modules if module.path is not None
    }
    intent_rule = agent_policy_rule(PY_AGENT_R007)
    broad_rule = agent_policy_rule(PY_AGENT_R008)
    findings: list[AspPythonFinding] = []
    for branch in facts.branches:
        if branch.has_intent_doc:
            findings.extend(
                _broad_branch_findings(
                    branch,
                    facts=facts,
                    rule_id=PY_AGENT_R008,
                    pack_id=pack_id,
                    modules_by_path=modules_by_path,
                )
            )
            continue
        module = modules_by_path.get(branch.path)
        namespace = ".".join(branch.namespace)
        findings.append(
            AspPythonFinding(
                rule_id=intent_rule.rule_id,
                pack_id=pack_id,
                severity=intent_rule.severity,
                title=intent_rule.title,
                summary=(
                    f"{branch.path} owns {branch.child_count} child modules "
                    f"under Python reasoning-tree branch {namespace!r} without "
                    "an intent docstring."
                ),
                location=path_location(branch.path),
                requirement=intent_rule.requirement,
                source_line=None if module is None else module.source_line(1),
                label="add a package intent docstring to this branch",
                labels=dict(intent_rule.labels),
            )
        )
        findings.extend(
            _broad_branch_findings(
                branch,
                facts=facts,
                rule_id=broad_rule.rule_id,
                pack_id=pack_id,
                modules_by_path=modules_by_path,
            )
        )
    return tuple(findings)


def _broad_branch_findings(
    branch: PythonReasoningTreeBranch,
    *,
    facts: PythonReasoningTreeFacts,
    rule_id: str,
    pack_id: str,
    modules_by_path: dict[str, PythonModuleReport],
) -> tuple[AspPythonFinding, ...]:
    child_nodes = _branch_child_nodes(branch, facts)
    public_child_count = sum(node.has_public_surface for node in child_nodes)
    effective_lines = sum(node.effective_code_lines for node in child_nodes)
    if not _branch_needs_owner_map(
        branch,
        public_child_count=public_child_count,
        effective_lines=effective_lines,
    ):
        return ()
    module = modules_by_path.get(branch.path)
    if _module_documents_owner_map(module):
        return ()
    rule = agent_policy_rule(rule_id)
    namespace = ".".join(branch.namespace)
    return (
        AspPythonFinding(
            rule_id=rule.rule_id,
            pack_id=pack_id,
            severity=rule.severity,
            title=rule.title,
            summary=(
                f"{branch.path} owns {branch.child_count} child modules, "
                f"{public_child_count} public child modules, and "
                f"{effective_lines} effective child lines under "
                f"Python reasoning-tree branch {namespace!r}."
            ),
            location=path_location(branch.path),
            requirement=rule.requirement,
            source_line=None if module is None else module.source_line(1),
            label="split this branch or document the owner map",
            labels=dict(rule.labels),
        ),
    )


def _branch_child_nodes(
    branch: PythonReasoningTreeBranch,
    facts: PythonReasoningTreeFacts,
) -> tuple[PythonReasoningTreeNode, ...]:
    return tuple(
        node
        for node in facts.nodes
        if node.parent_namespace == branch.namespace and node.kind == "module"
    )


def _module_documents_owner_map(module: object) -> bool:
    text_candidates: list[str] = []
    for attr in ("docstring", "module_docstring", "source", "source_text", "content"):
        value = getattr(module, attr, None)
        if isinstance(value, str):
            text_candidates.append(value)

    for attr in ("path", "source_path"):
        path = getattr(module, attr, None)
        if path is None:
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                text_candidates.append(handle.read(8192))
        except (OSError, TypeError):
            continue

    return any(_text_documents_owner_map(text) for text in text_candidates)


def _text_documents_owner_map(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("owner map", "owner-map", "owner_map"))


def _branch_needs_owner_map(
    branch: PythonReasoningTreeBranch,
    *,
    public_child_count: int,
    effective_lines: int,
) -> bool:
    if branch.has_public_surface:
        return False
    if branch.child_count < _MAX_AGENT_BRANCH_CHILDREN:
        return False
    return (
        public_child_count >= _MIN_AGENT_BRANCH_PUBLIC_CHILDREN
        or effective_lines >= _MIN_AGENT_BRANCH_EFFECTIVE_LINES
    )


def _module_documents_owner_map(module: PythonModuleReport | None) -> bool:
    if module is None or module.module_docstring is None:
        return False
    normalized = module.module_docstring.lower().replace("-", " ")
    return "owner map" in normalized


def _reasoning_tree_import_roots(scope: PythonProjectHarnessScope) -> tuple[Path, ...]:
    if scope.source_paths:
        return scope.source_paths
    return scope.monitored_paths
