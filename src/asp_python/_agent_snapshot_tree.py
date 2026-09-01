"""Compact parser-backed tree section for Agent snapshots."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .verification.facts import is_test_path, verification_reasoning_tree_facts

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonProjectMetadata,
        PythonReasoningTreeBranch,
        PythonReasoningTreeFacts,
        PythonReasoningTreeImportEdge,
        PythonReasoningTreeNode,
        PythonReasoningTreeShadow,
    )

    from ._model import AspPythonReport


@dataclass(frozen=True, slots=True)
class _SnapshotTreeLimits:
    branch_lines: int = 24
    import_edges: int = 8
    public_owners: int = 12
    children: int = 8
    public_names: int = 6


_LIMITS = _SnapshotTreeLimits()


@dataclass(frozen=True, slots=True)
class _SourceTreeFacts:
    nodes: tuple[PythonReasoningTreeNode, ...]
    branches: tuple[PythonReasoningTreeBranch, ...]
    import_edges: tuple[PythonReasoningTreeImportEdge, ...]
    shadows: tuple[PythonReasoningTreeShadow, ...]
    test_count: int


def render_python_agent_snapshot_tree(
    report: AspPythonReport,
    *,
    target: str,
) -> str:
    """Render the capped parser reasoning-tree section for an Agent snapshot."""

    return _SnapshotTreeRenderer(report, target, _LIMITS).render()


@dataclass(frozen=True, slots=True)
class _SnapshotTreeRenderer:
    report: AspPythonReport
    target: str
    limits: _SnapshotTreeLimits

    @property
    def project_root(self) -> Path | None:
        if self.report.project_resolution is None:
            return None
        return self.report.project_resolution.project_root

    def render(self) -> str:
        facts = verification_reasoning_tree_facts(self.report)
        if not facts.nodes and facts.project_metadata is None:
            return ""
        source = self.source_tree_facts(facts)
        lines = self.initial_lines(source)
        if facts.project_metadata is not None:
            lines.extend(self.metadata_lines(facts.project_metadata))
        self.add_branches(lines, source.branches)
        self.add_public_owners(lines, source.nodes)
        self.add_imports(lines, source.import_edges)
        self.add_shadows(lines, source.shadows)
        return "\n".join(lines) + "\n"

    def source_tree_facts(
        self,
        facts: PythonReasoningTreeFacts,
    ) -> _SourceTreeFacts:
        nodes = tuple(node for node in facts.nodes if not self.is_test(node.path))
        return _SourceTreeFacts(
            nodes=nodes,
            branches=tuple(
                branch for branch in facts.branches if not self.is_test(branch.path)
            ),
            import_edges=tuple(
                edge
                for edge in facts.import_edges
                if not self.is_test(edge.importer_path)
                and not self.is_test(edge.imported_path)
            ),
            shadows=tuple(
                shadow
                for shadow in facts.shadowed_module_sources
                if not self.is_test(shadow.module_path)
                and not self.is_test(shadow.package_init_path)
            ),
            test_count=len(facts.nodes) - len(nodes),
        )

    def initial_lines(self, source: _SourceTreeFacts) -> list[str]:
        return [
            f"[tree] {self.target} python",
            self.module_summary(
                source_nodes=source.nodes,
                test_count=source.test_count,
                branch_count=len(source.branches),
                dependency_count=len(source.import_edges),
                shadowed_count=len(source.shadows),
            ),
        ]

    def module_summary(
        self,
        *,
        source_nodes: Sequence[PythonReasoningTreeNode],
        test_count: int,
        branch_count: int,
        dependency_count: int,
        shadowed_count: int,
    ) -> str:
        parts = [f"source={len(source_nodes)}"]
        root_count = sum(1 for node in source_nodes if node.parent_namespace is None)
        self.append_metric(parts, "tests", test_count, test_count > 0)
        self.append_metric(parts, "roots", root_count, root_count > 1)
        self.append_metric(parts, "branches", branch_count, branch_count > 0)
        self.append_metric(parts, "imports", dependency_count, dependency_count > 0)
        self.append_metric(parts, "shadowed", shadowed_count, shadowed_count > 0)
        return "Modules: " + " ".join(parts)

    def metadata_lines(self, metadata: PythonProjectMetadata) -> list[str]:
        lines = ["Project:"]
        self.add_metadata_identity(lines, metadata)
        self.add_metadata_import_names(lines, metadata)
        self.add_metadata_package_roots(lines, metadata)
        self.add_metadata_scripts(lines, metadata)
        self.add_metadata_entry_points(lines, metadata)
        if metadata.pytest_options.enables_asp_python:
            lines.append("- pytest=python-project-harness")
        return lines

    def add_metadata_identity(
        self,
        lines: list[str],
        metadata: PythonProjectMetadata,
    ) -> None:
        identity = []
        if metadata.project_name:
            identity.append(f"name={metadata.project_name}")
        if metadata.requires_python:
            identity.append(f"requires-python={metadata.requires_python}")
        if metadata.build_backend:
            identity.append(f"build-backend={metadata.build_backend}")
        if identity:
            lines.append("- " + " ".join(identity))

    def add_metadata_import_names(
        self,
        lines: list[str],
        metadata: PythonProjectMetadata,
    ) -> None:
        import_names = (*metadata.import_names, *metadata.import_namespaces)
        if import_names:
            lines.append(
                "- import-names="
                + self.compact_values(tuple(item.name for item in import_names))
            )

    def add_metadata_package_roots(
        self,
        lines: list[str],
        metadata: PythonProjectMetadata,
    ) -> None:
        if metadata.package_roots:
            lines.append(
                "- package-roots="
                + self.compact_values(
                    tuple(self.display(path) for path in metadata.package_roots)
                )
            )

    def add_metadata_scripts(
        self,
        lines: list[str],
        metadata: PythonProjectMetadata,
    ) -> None:
        script_names = tuple(script.name for script in metadata.scripts)
        if script_names:
            lines.append("- scripts=" + self.compact_values(script_names))

    def add_metadata_entry_points(
        self,
        lines: list[str],
        metadata: PythonProjectMetadata,
    ) -> None:
        entry_points = tuple(
            f"{entry.group}:{entry.name}" for entry in metadata.entry_points
        )
        if entry_points:
            lines.append("- entry-points=" + self.compact_values(entry_points))

    def add_branches(
        self,
        lines: list[str],
        branches: Sequence[PythonReasoningTreeBranch],
    ) -> None:
        if not branches:
            return
        lines.append("Branches:")
        lines.extend(
            self.limited_lines(
                (self.render_branch(branch) for branch in branches),
                limit=self.limits.branch_lines,
                omitted_label="branches",
            )
        )

    def add_public_owners(
        self,
        lines: list[str],
        nodes: Sequence[PythonReasoningTreeNode],
    ) -> None:
        public_nodes = tuple(node for node in nodes if node.has_public_surface)
        if not public_nodes:
            return
        lines.append("PublicOwners:")
        lines.extend(
            self.limited_lines(
                (self.render_public_owner(node) for node in public_nodes),
                limit=self.limits.public_owners,
                omitted_label="public owners",
            )
        )

    def add_imports(
        self,
        lines: list[str],
        edges: Sequence[PythonReasoningTreeImportEdge],
    ) -> None:
        if not edges:
            return
        lines.append("Imports:")
        lines.extend(
            self.limited_lines(
                (self.render_import_edge(edge) for edge in edges),
                limit=self.limits.import_edges,
                omitted_label="imports",
            )
        )

    def add_shadows(
        self,
        lines: list[str],
        shadows: Sequence[PythonReasoningTreeShadow],
    ) -> None:
        if not shadows:
            return
        lines.append("Shadows:")
        lines.extend(self.render_shadow(shadow) for shadow in shadows)

    def render_branch(self, branch: PythonReasoningTreeBranch) -> str:
        flags = ["doc" if branch.has_intent_doc else "no-doc"]
        if branch.has_public_surface:
            flags.append("public")
        return (
            f"- {self.display(branch.path)} owner={self.namespace(branch.namespace)} "
            f"flags={','.join(flags)} "
            f"children={self.compact_values(branch.child_names, limit=self.limits.children)}"
        )

    def render_public_owner(self, node: PythonReasoningTreeNode) -> str:
        flags = [node.kind, "doc" if node.has_intent_doc else "no-doc"]
        if node.child_names:
            flags.append(
                "children="
                + self.compact_values(node.child_names, limit=self.limits.children)
            )
        return (
            f"- {self.display(node.path)} owner={self.namespace(node.namespace)} "
            f"flags={','.join(flags)} "
            f"public={self.compact_values(node.public_names, limit=self.limits.public_names)} "
            f"lines={node.effective_code_lines}"
        )

    def render_import_edge(self, edge: PythonReasoningTreeImportEdge) -> str:
        import_label = edge.import_name
        if edge.bound_name and edge.bound_name != edge.import_name:
            import_label += f" as {edge.bound_name}"
        relation = "relative" if edge.is_relative else "absolute"
        return (
            f"- {self.display(edge.importer_path)} --{relation}:{import_label}--> "
            f"{self.display(edge.imported_path)}"
        )

    def render_shadow(self, shadow: PythonReasoningTreeShadow) -> str:
        return (
            f"- {self.namespace(shadow.namespace)}: "
            f"{self.display(shadow.module_path)} <-> {self.display(shadow.package_init_path)}"
        )

    def compact_values(self, values: Sequence[str], *, limit: int | None = None) -> str:
        limit = self.limits.children if limit is None else limit
        rendered = ",".join(values[:limit])
        omitted = len(values) - limit
        if omitted <= 0:
            return rendered
        return f"+{omitted}" if not rendered else f"{rendered},+{omitted}"

    def limited_lines(
        self,
        lines: Iterable[str],
        *,
        limit: int,
        omitted_label: str,
    ) -> list[str]:
        values = list(lines)
        rendered = values[:limit]
        omitted = len(values) - limit
        if omitted > 0:
            rendered.append(f"... +{omitted} {omitted_label}")
        return rendered

    def display(self, path: str | Path) -> str:
        path = Path(path)
        if self.project_root is None:
            return str(path)
        try:
            return str(
                path.resolve(strict=False).relative_to(
                    self.project_root.resolve(strict=False)
                )
            )
        except ValueError:
            return str(path)

    def is_test(self, path: str | Path) -> bool:
        return is_test_path(self.display(path))

    @staticmethod
    def append_metric(
        parts: list[str],
        label: str,
        value: int,
        should_render: bool,
    ) -> None:
        if should_render:
            parts.append(f"{label}={value}")

    @staticmethod
    def namespace(namespace: Sequence[str]) -> str:
        return ".".join(namespace) if namespace else "<root>"
