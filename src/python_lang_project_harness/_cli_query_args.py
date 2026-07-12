"""Query command argument parsing for the Python harness CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._cli_query_arg_consume import (
    ProtocolArgError,
    QueryParseState,
    consume_query_arg,
)
from ._cli_query_flow_lite_args import (
    flow_lite_query_args_error,
    flow_lite_query_protocol_args,
    is_flow_lite_query_state,
)
from ._cli_query_hook_args import (
    is_broad_hook_query,
    owner_path_from_query_selector,
    selector_has_line_range,
)
from ._cli_query_tree_sitter_args import (
    is_tree_sitter_query_state,
    tree_sitter_query_args_error,
    tree_sitter_query_protocol_args,
)

if TYPE_CHECKING:
    from ._cli_args import ProtocolArgs


def parse_query_args(
    args_type: type[ProtocolArgs],
    args: list[str] | tuple[str, ...],
) -> ProtocolArgs:
    """Parse py-harness query arguments into protocol args."""

    if args and args[0] in {"--help", "-h"}:
        return args_type("help")
    state = QueryParseState()
    index = 0
    while index < len(args):
        index = consume_query_arg(state, args, index)
        if isinstance(index, ProtocolArgError):
            return args_type("error", error=index.message)
    return _query_args_result(args_type, state)


def _query_args_result(
    args_type: type[ProtocolArgs],
    state: QueryParseState,
) -> ProtocolArgs:
    error = _query_args_error(state)
    if error is not None:
        return args_type("error", error=error)
    if is_broad_hook_query(state.from_hook, state.selector, state.terms):
        return args_type(
            "search",
            view="lexical",
            query=",".join(state.terms),
            query_set=tuple(state.terms),
            project_root=_query_project_root(state),
            package_path=state.package_path,
            workspace=state.workspace,
            pipes=tuple(state.surfaces),
            render_mode=state.render_mode,
            source_version=state.source_version,
        )
    if is_flow_lite_query_state(state):
        return flow_lite_query_protocol_args(args_type, state)
    if is_tree_sitter_query_state(state):
        return tree_sitter_query_protocol_args(args_type, state)
    owner_path = (
        owner_path_from_query_selector(state.selector)
        if state.selector is not None
        else state.positionals[0]
    )
    return args_type(
        "query",
        owner_path=owner_path,
        selector=state.selector,
        query_set=tuple(state.terms),
        project_root=_query_project_root(state),
        package_path=state.package_path,
        workspace=state.workspace,
        json=state.json_output,
        names_only=_query_names_only(state),
        code_only=state.code_only,
        source_version=state.source_version,
        render_mode=state.render_mode,
    )


def _query_args_error(state: QueryParseState) -> str | None:
    if state.from_hook is not None and state.from_hook != "owner-local-projection":
        return f"unsupported query hook route: {state.from_hook}"
    if _query_has_positional_workspace(
        state
    ) and not _query_allows_positional_workspace(state):
        return "query does not accept positional WORKSPACE; use --workspace <workspace-root>"
    if is_flow_lite_query_state(state):
        return flow_lite_query_args_error(state)
    if is_tree_sitter_query_state(state):
        return tree_sitter_query_args_error(state)
    if not state.selector and not state.positionals:
        if state.names_only and state.terms:
            return (
                "query --names-only requires an owner selector; workspace term discovery is "
                "`search lexical '<term>' owner --workspace <workspace-root> --view seeds`"
            )
        return "query requires an owner path"
    if not state.terms and state.from_hook != "owner-local-projection":
        return "query requires at least one --term"
    broad_hook_query = is_broad_hook_query(state.from_hook, state.selector, state.terms)
    if state.json_output and state.code_only:
        return "--code cannot be combined with --json"
    if state.names_only and state.code_only:
        return "--code cannot be combined with --names-only"
    if state.surfaces and not broad_hook_query:
        return "query --surface is Rust ASP search-owned; Python query accepts exact owner-local projection only"
    if state.render_mode is not None and not broad_hook_query:
        return "query --view is Rust ASP search-owned; Python query accepts exact owner-local projection only"
    return None


def _query_project_root(state: QueryParseState) -> Path | None:
    if state.workspace_root is not None:
        return state.workspace_root
    return None


def _query_has_positional_workspace(state: QueryParseState) -> bool:
    if state.selector is None:
        return len(state.positionals) > 1
    return bool(state.positionals)


def _query_allows_positional_workspace(state: QueryParseState) -> bool:
    return state.catalog is not None and state.tree_sitter_query is None


def _query_names_only(state: QueryParseState) -> bool:
    if state.names_only:
        return True
    return bool(
        not state.terms
        and state.from_hook == "owner-local-projection"
        and not state.code_only
        and not state.json_output
        and not selector_has_line_range(state.selector)
    )
