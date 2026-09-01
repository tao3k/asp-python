"""Tree-sitter query argument helpers for the Python CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def is_tree_sitter_query_state(state: Any) -> bool:
    return state.catalog is not None or state.tree_sitter_query is not None


def tree_sitter_query_args_error(state: Any) -> str | None:
    if state.catalog is not None and state.tree_sitter_query is not None:
        return "query accepts only one of --catalog or --treesitter-query"
    if state.workspace_root is not None and state.positionals:
        return (
            "query accepts either --workspace <workspace-root> or one positional "
            "WORKSPACE, not both"
        )
    if len(state.positionals) > 1:
        return "query accepts at most one positional WORKSPACE"
    if state.surfaces:
        return "query --surface is Rust ASP search-owned; Python query accepts tree-sitter projection only"
    if state.render_mode is not None:
        return "query --view is Rust ASP search-owned; Python query accepts tree-sitter projection only"
    return None


def tree_sitter_query_protocol_args(args_type: type[Any], state: Any) -> Any:
    return args_type(
        "query",
        selector=state.selector,
        catalog=state.catalog,
        tree_sitter_query=state.tree_sitter_query,
        asp_syntax_query_captures=tuple(state.asp_syntax_query_captures),
        asp_syntax_query_node_types=tuple(state.asp_syntax_query_node_types),
        asp_syntax_query_fields=tuple(state.asp_syntax_query_fields),
        asp_syntax_query_predicates=tuple(state.asp_syntax_query_predicates),
        query_set=tuple(state.terms),
        project_root=_tree_sitter_query_project_root(state),
        package_path=state.package_path,
        workspace=state.workspace or bool(state.positionals),
        json=state.json_output,
    )


def _tree_sitter_query_project_root(state: Any) -> Path | None:
    if state.workspace_root is not None:
        return state.workspace_root
    if len(state.positionals) == 1:
        return Path(state.positionals[0])
    return None
