"""Query command argument parsing for the Python harness CLI."""

from __future__ import annotations

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
    """Parse asp-python query arguments into protocol args."""

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
    if is_flow_lite_query_state(state):
        return flow_lite_query_protocol_args(args_type, state)
    if is_tree_sitter_query_state(state):
        return tree_sitter_query_protocol_args(args_type, state)
    return args_type(
        "error",
        error=(
            "exact source projection is ASP-owned; use `asp python query "
            "--selector <exact-structural-selector> --projection "
            "source|callable-skeleton --workspace <workspace-root>`"
        ),
    )


def _query_args_error(state: QueryParseState) -> str | None:
    if _query_has_positional_workspace(
        state
    ) and not _query_allows_positional_workspace(state):
        return "query does not accept positional WORKSPACE; use --workspace <workspace-root>"
    if is_flow_lite_query_state(state):
        return flow_lite_query_args_error(state)
    if is_tree_sitter_query_state(state):
        return tree_sitter_query_args_error(state)
    if not state.selector and not state.positionals:
        return "query requires an owner path"
    if not state.terms and state.selector is None:
        return "query requires at least one --term"
    if state.surfaces:
        return "query --surface is Rust ASP search-owned; Python query accepts exact owner-local projection only"
    if state.render_mode is not None:
        return "query --view is Rust ASP search-owned; Python query accepts exact owner-local projection only"
    return None


def _query_has_positional_workspace(state: QueryParseState) -> bool:
    if state.selector is None:
        return len(state.positionals) > 1
    return bool(state.positionals)


def _query_allows_positional_workspace(state: QueryParseState) -> bool:
    return state.catalog is not None and state.tree_sitter_query is None
