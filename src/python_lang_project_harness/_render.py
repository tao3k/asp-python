"""Compact snapshot rendering for Python harness diagnostics."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity
from python_lang_parser._reasoning_tree import python_reasoning_tree_facts

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import (
        PythonProjectEntryPoint,
        PythonProjectImportName,
        PythonProjectMetadata,
        PythonProjectScript,
        PythonReasoningTreeImportEdge,
        PythonReasoningTreeNode,
    )

    from ._model import PythonHarnessFinding, PythonHarnessReport


def _compact_render_fields(fields: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in fields.items()
        if value is not None and value != [] and value != ""
    }


def _render_line_fields(fields: dict[str, object]) -> str:
    return " ".join(
        f"{key}={_line_protocol_field_value(value)}"
        for key, value in fields.items()
        if value != [] and value != ""
    )


def _line_protocol_field_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def render_python_lang_harness(
    report: PythonHarnessReport,
    *,
    severities: frozenset[PythonDiagnosticSeverity] | None = None,
    include_advice: bool = True,
) -> str:
    """Render a compact diagnostic report for humans and repair workflows."""

    project_root = _report_project_root(report)
    blocking_findings = report.blocking_findings(severities=severities)
    advice_findings = (
        _deduplicate_advice_findings(
            report.advisory_findings(),
            blocking_findings=blocking_findings,
        )
        if include_advice
        else ()
    )
    if blocking_findings:
        rendered = _render_failure_frontier(
            report,
            blocking_findings,
            project_root=project_root,
        )
        if advice_findings:
            rendered += "\n[advice]\n" + _render_findings(
                advice_findings,
                project_root=project_root,
            )
        return rendered
    if advice_findings:
        return "[advice]\n" + _render_findings(
            advice_findings,
            project_root=project_root,
        )
    return _render_ok_header(report)


def render_python_lang_harness_json(report: PythonHarnessReport) -> str:
    """Render a structured JSON diagnostic report for tool consumers."""

    return json.dumps(report.to_dict(), separators=(",", ":"), sort_keys=True)


def render_python_lang_harness_advice(report: PythonHarnessReport) -> str:
    """Render non-blocking advisory findings for agent-guided repair."""

    advice_findings = _deduplicate_advice_findings(
        report.advisory_findings(),
        blocking_findings=report.blocking_findings(),
    )
    if not advice_findings:
        return ""
    return _render_findings(
        advice_findings,
        project_root=_report_project_root(report),
    )


def render_python_reasoning_tree(
    report: PythonHarnessReport,
    *,
    max_nodes: int = 80,
    max_edges: int = 80,
) -> str:
    """Render a compact project reasoning tree for repair-oriented agents."""

    facts = python_reasoning_tree_facts(
        report.modules,
        import_roots=_reasoning_tree_import_roots(report),
        project_root=(
            None
            if report.project_resolution is None
            else report.project_resolution.project_root
        ),
        project_metadata=(
            None
            if report.project_resolution is None
            else report.project_resolution.project_metadata
        ),
    )
    project_root = _report_project_root(report)
    target = ", ".join(
        _render_display_path(path, project_root=project_root)
        for path in report.root_paths
    )
    lines = [f"[tree] {target} python"]
    if facts.shadowed_module_sources:
        lines.append("[shadows]")
        for shadow in facts.shadowed_module_sources:
            namespace = ".".join(shadow.namespace)
            lines.append(
                f"- {namespace}: "
                f"{_render_display_path(shadow.module_path, project_root=project_root)}"
                " <-> "
                f"{_render_display_path(shadow.package_init_path, project_root=project_root)}"
            )
    if facts.project_metadata is not None:
        lines.extend(
            _render_reasoning_tree_project_metadata(
                facts.project_metadata,
                project_root=project_root,
            )
        )
    lines.append("[nodes]")
    for node in facts.nodes[:max_nodes]:
        lines.append(_render_reasoning_tree_node(node, project_root=project_root))
    omitted = len(facts.nodes) - max_nodes
    if omitted > 0:
        lines.append(f"... {omitted} more nodes")
    if facts.import_edges:
        lines.append("[imports]")
        for edge in facts.import_edges[:max_edges]:
            lines.append(_render_reasoning_tree_import_edge(edge))
        omitted_edges = len(facts.import_edges) - max_edges
        if omitted_edges > 0:
            lines.append(f"... {omitted_edges} more imports")
    return "\n".join(lines) + "\n"


def _render_ok_header(report: PythonHarnessReport) -> str:
    project_root = _report_project_root(report)
    target = ", ".join(
        _render_display_path(path, project_root=project_root)
        for path in report.root_paths
    )
    return (
        f"[ok] {target} python\n"
        f"Files: {report.file_count} Parsed: {report.parsed_count}\n"
    )


def _render_findings(
    findings: tuple[PythonHarnessFinding, ...],
    *,
    project_root: Path | None,
) -> str:
    return (
        "\n\n".join(
            _render_finding(finding, project_root=project_root).rstrip("\n")
            for finding in findings
        )
        + "\n"
    )


def _render_failure_frontier(
    report: PythonHarnessReport,
    findings: tuple[PythonHarnessFinding, ...],
    *,
    project_root: Path | None,
) -> str:
    lines = [
        (
            f"[fail] python blockingFindings={len(findings)} "
            f"parsed={report.parsed_count}/{report.file_count}"
        )
    ]
    for finding in findings[:3]:
        fields = {
            "rule": finding.rule_id,
            "severity": finding.severity.value,
            "path": _render_display_path(
                finding.location.path or "<memory>",
                project_root=project_root,
            ),
            "line": finding.location.line,
            "column": finding.location.column + 1,
        }
        lines.append(f"|failureFrontier {_render_line_fields(fields)}")
        lines.append(f"|message {_failure_frontier_text(finding.title)}")
        if finding.summary:
            lines.append(f"|summary {_failure_frontier_text(finding.summary)}")
        if finding.label:
            lines.append(f"|repair {_failure_frontier_text(finding.label)}")
        selector = _failure_frontier_selector(finding, project_root=project_root)
        if selector is not None:
            lines.append(f"|hotBlock selector={selector} reason=blocking-finding")
    if len(findings) > 3:
        lines.append(f"|more blockingFindings={len(findings) - 3}")
    return "\n".join(lines) + "\n"


def _failure_frontier_selector(
    finding: PythonHarnessFinding,
    *,
    project_root: Path | None,
) -> str | None:
    if finding.location.path is None:
        return None
    line = max(finding.location.line, 1)
    path = _render_display_path(finding.location.path, project_root=project_root)
    return f"{path}:{line}:{line}"


def _failure_frontier_text(value: str) -> str:
    return " ".join(value.split())


def _render_finding(
    finding: PythonHarnessFinding,
    *,
    project_root: Path | None,
) -> str:
    path = _render_display_path(
        finding.location.path or "<memory>",
        project_root=project_root,
    )
    line = finding.location.line
    column = finding.location.column
    severity = finding.severity.value.title()
    display_column = column + 1
    rendered = (
        f"[{finding.rule_id}] {severity}: {finding.title}\n"
        f"  --> {path}:{line}:{display_column}\n"
    )
    if finding.source_line:
        pointer_column = max(column, 0)
        rendered += (
            f"{line:>4} | {finding.source_line}\n"
            f"     | {' ' * pointer_column}`- {finding.label}\n"
        )
    else:
        rendered += f"     | {finding.label}\n"
    rendered += f"     | Required: {finding.requirement}\n"
    software_criteria = _software_criterion_labels(finding)
    if software_criteria:
        rendered += f"     | Criteria: {software_criteria}\n"
    return rendered


def _software_criterion_labels(finding: PythonHarnessFinding) -> str:
    value = finding.labels.get("softwareCriteria")
    if not value:
        return ""
    if isinstance(value, str):
        return ",".join(_format_software_criterion(item) for item in value.split(","))
    if isinstance(value, (list, tuple)):
        return ",".join(_format_software_criterion(str(item)) for item in value)
    return _format_software_criterion(str(value))


def _format_software_criterion(criterion_id: str) -> str:
    criterion_id = criterion_id.strip()
    if criterion_id.startswith("software-criterion/"):
        return criterion_id
    return f"software-criterion/{criterion_id}"


def _reasoning_tree_import_roots(report: PythonHarnessReport) -> tuple[Path | str, ...]:
    if report.project_resolution is None:
        return report.root_paths
    if report.project_resolution.source_paths:
        return report.project_resolution.source_paths
    return report.project_resolution.monitored_paths


def _report_project_root(report: PythonHarnessReport) -> Path | None:
    if report.project_resolution is None:
        return None
    return report.project_resolution.project_root


def _render_reasoning_tree_node(
    node: PythonReasoningTreeNode,
    *,
    project_root: Path | None,
) -> str:
    depth = max(len(node.namespace) - 1, 0)
    indent = "  " * depth
    namespace = ".".join(node.namespace) if node.namespace else "<root>"
    flags = [
        node.kind,
        "doc" if node.has_intent_doc else "no-doc",
        "public" if node.has_public_surface else "internal",
    ]
    if node.child_names:
        flags.append("children=" + ",".join(node.child_names))
    export_flag = _render_reasoning_tree_export_flag(node)
    if export_flag is not None:
        flags.append(export_flag)
    if not node.is_valid:
        flags.append("invalid")
    path = _render_display_path(node.path, project_root=project_root)
    return f"{indent}- {namespace} ({'; '.join(flags)}) {path}"


def _render_reasoning_tree_project_metadata(
    project_metadata: PythonProjectMetadata,
    *,
    project_root: Path | None,
) -> list[str]:
    lines = ["[project]"]
    lines.append(_render_project_name_line(project_metadata))
    lines.extend(
        line
        for line in (
            _render_project_import_names_line(project_metadata.import_names),
            _render_project_import_namespaces_line(
                project_metadata.import_namespaces,
            ),
            _render_project_package_roots_line(
                project_metadata.package_roots,
                project_root=project_root,
            ),
            _render_project_scripts_line(project_metadata.scripts),
            _render_project_entry_points_line(project_metadata.entry_points),
        )
        if line is not None
    )
    return lines


def _render_project_name_line(project_metadata: PythonProjectMetadata) -> str:
    name = project_metadata.project_name or "<unnamed>"
    requires_python = project_metadata.requires_python or "<any>"
    return f"- name={name} requires-python={requires_python}"


def _render_project_import_names_line(
    import_names: Sequence[PythonProjectImportName],
) -> str | None:
    if not import_names:
        return None
    return "- import-names=" + _render_project_import_names(import_names)


def _render_project_import_namespaces_line(
    import_namespaces: Sequence[PythonProjectImportName],
) -> str | None:
    if not import_namespaces:
        return None
    return "- import-namespaces=" + _render_project_import_names(import_namespaces)


def _render_project_package_roots_line(
    package_roots: Sequence[Path],
    *,
    project_root: Path | None,
) -> str | None:
    if not package_roots:
        return None
    return "- package-roots=" + _render_compact_name_list(
        tuple(
            _render_display_path(path, project_root=project_root)
            for path in package_roots
        ),
        max_names=4,
    )


def _render_project_scripts_line(
    scripts: Sequence[PythonProjectScript],
) -> str | None:
    if not scripts:
        return None
    return "- scripts=" + _render_compact_name_list(
        tuple(script.name for script in scripts),
        max_names=6,
    )


def _render_project_entry_points_line(
    entry_points: Sequence[PythonProjectEntryPoint],
) -> str | None:
    if not entry_points:
        return None
    return "- entry-points=" + _render_compact_name_list(
        tuple(f"{entry.group}:{entry.name}" for entry in entry_points),
        max_names=6,
    )


def _render_project_import_names(
    import_names: Sequence[PythonProjectImportName],
) -> str:
    names = tuple(
        (import_name.name + (";private" if import_name.is_private else ""))
        for import_name in import_names
    )
    return _render_compact_name_list(names)


def _render_reasoning_tree_export_flag(node: PythonReasoningTreeNode) -> str | None:
    if node.public_names:
        return "exports=" + _render_compact_name_list(node.public_names)
    if node.export_contract_kind == "static":
        return "exports=none"
    if node.export_contract_kind == "dynamic":
        return "exports=dynamic"
    return None


def _render_compact_name_list(names: tuple[str, ...], *, max_names: int = 6) -> str:
    shown = names[:max_names]
    rendered = ",".join(shown)
    omitted = len(names) - len(shown)
    if omitted > 0:
        rendered += f",+{omitted}"
    return rendered


def _render_reasoning_tree_import_edge(edge: PythonReasoningTreeImportEdge) -> str:
    importer = ".".join(edge.importer_namespace)
    imported = ".".join(edge.imported_namespace)
    scope = "module" if edge.scope == "" else edge.scope
    relation = "relative" if edge.is_relative else "absolute"
    return f"- {importer} -> {imported} ({relation}; {scope}; as {edge.bound_name})"


def _render_display_path(path: Path | str, *, project_root: Path | None) -> str:
    rendered = str(path)
    if project_root is None:
        return rendered
    path_obj = Path(path)
    if not path_obj.is_absolute():
        return rendered
    try:
        root = project_root.resolve(strict=False)
        resolved_path = path_obj.resolve(strict=False)
        if os.path.commonpath((str(root), str(resolved_path))) != str(root):
            return rendered
        relative_path = os.path.relpath(resolved_path, root)
    except (OSError, ValueError):
        return rendered
    if relative_path == ".":
        return "."
    return relative_path


def _deduplicate_advice_findings(
    advice_findings: tuple[PythonHarnessFinding, ...],
    *,
    blocking_findings: tuple[PythonHarnessFinding, ...],
) -> tuple[PythonHarnessFinding, ...]:
    blocking_keys = {_finding_key(finding) for finding in blocking_findings}
    return tuple(
        finding
        for finding in advice_findings
        if _finding_key(finding) not in blocking_keys
    )


def _finding_key(finding: PythonHarnessFinding) -> tuple[str, str | None, int, int]:
    return (
        finding.rule_id,
        finding.location.path,
        finding.location.line,
        finding.location.column,
    )
