"""Native Python AST projection into tree-sitter-compatible captures."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from ._python_expr import _expr
from ._semantic_search_common import semantic_search_display_path
from ._tree_sitter_query_model import (
    LEAF_TREE_SITTER_QUERY_NODES,
    MAX_SYNTAX_QUERY_ROWS,
    SUPPORTED_TREE_SITTER_QUERY_NODES,
    SyntaxQueryProjection,
    SyntaxQueryRow,
    SyntaxQuerySelector,
    node_span,
    selector_matches,
    terms_match,
)
from ._tree_sitter_query_predicates import (
    SyntaxQueryPredicate,
    syntax_predicates_match,
)
from ._tree_sitter_query_projection_capture import (
    call_capture as _call_capture,
)
from ._tree_sitter_query_projection_capture import (
    call_capture_node as _call_capture_node,
)
from ._tree_sitter_query_projection_capture import (
    capture_field as _capture_field,
)
from ._tree_sitter_query_projection_capture import (
    capture_node_type as _capture_node_type,
)
from ._tree_sitter_query_projection_capture import (
    decorator_capture as _decorator_capture,
)
from ._tree_sitter_query_projection_capture import (
    first_capture as _first_capture,
)
from ._tree_sitter_query_projection_source import (
    ResolvedSelectorSource,
    SyntaxSource,
    effective_selector,
    resolve_selector_source,
    syntax_sources,
)

if TYPE_CHECKING:
    from ._model import AspPythonReport


def project_tree_sitter_query(
    report: AspPythonReport,
    project_root: Path,
    query_node_types: tuple[str, ...],
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    predicates: tuple[SyntaxQueryPredicate, ...],
    terms: list[str],
    selector: SyntaxQuerySelector | None,
) -> SyntaxQueryProjection:
    requested_nodes = frozenset(query_node_types)
    active_nodes = requested_nodes & SUPPORTED_TREE_SITTER_QUERY_NODES
    unsupported_nodes = (
        sorted(
            node
            for node in requested_nodes
            if node not in SUPPORTED_TREE_SITTER_QUERY_NODES
            and node not in LEAF_TREE_SITTER_QUERY_NODES
        )
        if not active_nodes
        else []
    )
    resolved_selector_source = resolve_selector_source(project_root, selector)
    rows: list[SyntaxQueryRow] = []
    for source in syntax_sources(report, resolved_selector_source):
        rows.extend(
            _module_syntax_query_rows(
                source,
                project_root,
                active_nodes,
                captures,
                fields,
                predicates,
                terms,
                selector,
                resolved_selector_source,
            )
        )
    rows.sort(key=lambda row: (row.path, row.item_start_line, row.start_line, row.name))
    selected = rows[:MAX_SYNTAX_QUERY_ROWS]
    return SyntaxQueryProjection(
        rows=selected,
        total_matches=len(rows),
        truncated=len(rows) > len(selected),
        unsupported_nodes=unsupported_nodes,
    )


def _module_syntax_query_rows(
    module: SyntaxSource,
    project_root: Path,
    active_nodes: frozenset[str],
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    predicates: tuple[SyntaxQueryPredicate, ...],
    terms: list[str],
    selector: SyntaxQuerySelector | None,
    resolved_selector_source: ResolvedSelectorSource | None,
) -> list[SyntaxQueryRow]:
    if module.path is None:
        return []
    owner_path = semantic_search_display_path(module.path, project_root)
    effective = effective_selector(
        owner_path,
        selector,
        module,
        resolved_selector_source,
    )
    try:
        tree = ast.parse("\n".join(module.source_lines))
    except SyntaxError:
        return []
    rows: list[SyntaxQueryRow] = []
    for node in ast.walk(tree):
        row = _row_for_ast_node(
            module, owner_path, active_nodes, captures, fields, node
        )
        if row is not None:
            rows.append(row)
        rows.extend(
            _rows_for_ast_node_extras(
                module, owner_path, active_nodes, captures, fields, node
            )
        )
    return [
        row
        for row in rows
        if selector_matches(row, effective)
        and terms_match(row, terms)
        and syntax_predicates_match(row, predicates)
    ]


def _row_for_ast_node(
    module: SyntaxSource,
    owner_path: str,
    active_nodes: frozenset[str],
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    node: ast.AST,
) -> SyntaxQueryRow | None:
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        if "function_definition" not in active_nodes:
            return None
        return _syntax_row(
            module,
            owner_path,
            capture=_first_capture(captures, "function.name", "function.definition"),
            node_type="function_definition",
            name=node.name,
            node=node,
            item_node=node,
            fields=fields,
        )
    if isinstance(node, ast.ClassDef):
        if "class_definition" not in active_nodes:
            return None
        return _syntax_row(
            module,
            owner_path,
            capture=_first_capture(captures, "class.name", "class.definition"),
            node_type="class_definition",
            name=node.name,
            node=node,
            item_node=node,
            fields=fields,
        )
    if isinstance(node, ast.Call) and "call" in active_nodes:
        capture = _call_capture(captures, node)
        return _syntax_row(
            module,
            owner_path,
            capture=capture,
            node_type="call",
            name=_expr(node.func),
            node=_call_capture_node(capture, node),
            item_node=node,
            fields=fields,
        )
    return _import_or_control_row(
        module, owner_path, active_nodes, captures, fields, node
    )


def _rows_for_ast_node_extras(
    module: SyntaxSource,
    owner_path: str,
    active_nodes: frozenset[str],
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    node: ast.AST,
) -> list[SyntaxQueryRow]:
    rows: list[SyntaxQueryRow] = []
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        if "decorator" in active_nodes or "decorated_definition" in active_nodes:
            rows.extend(
                _decorator_rows(
                    module, owner_path, captures, fields, node, node.decorator_list
                )
            )
    if isinstance(node, ast.Call) and "keyword_argument" in active_nodes:
        rows.extend(_keyword_rows(module, owner_path, captures, fields, node))
    return rows


def _decorator_rows(
    module: SyntaxSource,
    owner_path: str,
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    item_node: ast.AST,
    decorators: list[ast.expr],
) -> list[SyntaxQueryRow]:
    rows: list[SyntaxQueryRow] = []
    for decorator in decorators:
        row = _syntax_row(
            module,
            owner_path,
            capture=_decorator_capture(captures, decorator),
            node_type="decorator",
            name=_expr(decorator),
            node=decorator,
            item_node=item_node,
            fields=fields,
        )
        if row is not None:
            rows.append(row)
    return rows


def _keyword_rows(
    module: SyntaxSource,
    owner_path: str,
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    call: ast.Call,
) -> list[SyntaxQueryRow]:
    rows: list[SyntaxQueryRow] = []
    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        row = _syntax_row(
            module,
            owner_path,
            capture=_first_capture(captures, "call.keyword"),
            node_type="keyword_argument",
            name=keyword.arg,
            node=keyword.value,
            item_node=call,
            fields=fields,
        )
        if row is not None:
            rows.append(row)
    return rows


def _import_or_control_row(
    module: SyntaxSource,
    owner_path: str,
    active_nodes: frozenset[str],
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    node: ast.AST,
) -> SyntaxQueryRow | None:
    if isinstance(node, ast.Import) and "import_statement" in active_nodes:
        return _syntax_row(
            module,
            owner_path,
            capture=_first_capture(captures, "import.name", "import.declaration"),
            node_type="import_statement",
            name=", ".join(alias.asname or alias.name for alias in node.names),
            node=node,
            item_node=node,
            fields=fields,
        )
    if isinstance(node, ast.ImportFrom) and "import_from_statement" in active_nodes:
        return _import_from_row(module, owner_path, captures, fields, node)
    control = _control_row_spec(active_nodes, captures, node)
    if control is None:
        return None
    node_type, capture, name_node = control
    return _syntax_row(
        module,
        owner_path,
        capture=capture,
        node_type=node_type,
        name=_expr(name_node),
        node=name_node,
        item_node=node,
        fields=fields,
    )


def _import_from_row(
    module: SyntaxSource,
    owner_path: str,
    captures: tuple[str, ...],
    fields: tuple[str, ...],
    node: ast.ImportFrom,
) -> SyntaxQueryRow | None:
    module_name = "." * node.level + (node.module or "")
    imported = ", ".join(alias.asname or alias.name for alias in node.names)
    name = f"{module_name}:{imported}" if module_name else imported
    return _syntax_row(
        module,
        owner_path,
        capture=_first_capture(
            captures, "import.name", "import.path", "import.declaration"
        ),
        node_type="import_from_statement",
        name=name,
        node=node,
        item_node=node,
        fields=fields,
    )


def _control_row_spec(
    active_nodes: frozenset[str],
    captures: tuple[str, ...],
    node: ast.AST,
) -> tuple[str, str | None, ast.AST] | None:
    if isinstance(node, ast.If) and "if_statement" in active_nodes:
        return (
            "if_statement",
            _first_capture(captures, "control.condition", "control.if"),
            node.test,
        )
    if isinstance(node, ast.For | ast.AsyncFor) and "for_statement" in active_nodes:
        return (
            "for_statement",
            _first_capture(captures, "control.loop", "control.iterable"),
            node.iter,
        )
    if isinstance(node, ast.While) and "while_statement" in active_nodes:
        return (
            "while_statement",
            _first_capture(captures, "control.condition", "control.loop"),
            node.test,
        )
    if isinstance(node, ast.With | ast.AsyncWith) and "with_statement" in active_nodes:
        target = node.items[0].context_expr if node.items else node
        return (
            "with_statement",
            _first_capture(captures, "context.manager", "control.with"),
            target,
        )
    if isinstance(node, ast.Try) and "try_statement" in active_nodes:
        return ("try_statement", _first_capture(captures, "control.exception"), node)
    if isinstance(node, ast.Match) and "match_statement" in active_nodes:
        return (
            "match_statement",
            _first_capture(captures, "control.subject", "control.match"),
            node.subject,
        )
    return None


def _syntax_row(
    module: SyntaxSource,
    owner_path: str,
    *,
    capture: str | None,
    node_type: str,
    name: str,
    node: ast.AST,
    item_node: ast.AST,
    fields: tuple[str, ...],
) -> SyntaxQueryRow | None:
    if capture is None:
        return None
    start_line, end_line = _capture_span(node, capture)
    item_start_line, item_end_line = node_span(item_node)
    return SyntaxQueryRow(
        capture=capture,
        capture_node=_capture_node_type(node_type, capture, node),
        capture_field=_capture_field(capture, fields),
        node=node_type,
        name=name,
        path=owner_path,
        start_line=start_line,
        end_line=end_line,
        item_start_line=item_start_line,
        item_end_line=item_end_line,
        item_code=_exact_item_code(module, item_start_line, item_end_line),
    )


def _capture_span(node: ast.AST, capture: str) -> tuple[int, int]:
    start_line, end_line = node_span(node)
    if capture.endswith(".name") or capture.endswith(".keyword"):
        return start_line, start_line
    return start_line, end_line


def _exact_item_code(
    module: SyntaxSource,
    start_line: int,
    end_line: int,
) -> str:
    raw_lines = module.source_lines[start_line - 1 : end_line]
    if not raw_lines:
        return ""
    return "\n".join(raw_lines)
