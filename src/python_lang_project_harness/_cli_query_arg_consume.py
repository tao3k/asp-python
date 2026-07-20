"""Low-level query option consumption for the Python CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ._cli_query_hook_args import (
    normalize_query_surfaces,
    normalize_query_view,
)
from ._cli_query_predicates import parse_asp_syntax_query_predicates
from ._tree_sitter_query_predicates import SyntaxQueryPredicate

QUERY_USAGE = (
    "usage: py-harness query <owner-path> --term <symbol> "
    "[--term <symbol>] [--workspace <workspace-root>] [--names-only] [--json] [--package PATH]; "
    "or py-harness query (--catalog ID | --treesitter-query EXPR) [<workspace-root>] [--workspace <workspace-root>] [--json]; "
    "or py-harness query --catalog flow-lite --where 'source.call=NAME sink.constructs=TYPE scope.fn=FUNCTION' [<workspace-root>] [--json] [--workspace <workspace-root>]"
)


class ProtocolArgError:
    """Small sentinel for parse errors without widening ProtocolArgs."""

    def __init__(self, message: str) -> None:
        self.message = message


@dataclass(slots=True)
class QueryParseState:
    json_output: bool = False
    names_only: bool = False
    code_only: bool = False
    package_path: Path | None = None
    workspace: bool = False
    workspace_root: Path | None = None
    selector: str | None = None
    catalog: str | None = None
    flow_lite_where: str | None = None
    tree_sitter_query: str | None = None
    asp_syntax_query_captures: list[str] = field(default_factory=list)
    asp_syntax_query_node_types: list[str] = field(default_factory=list)
    asp_syntax_query_fields: list[str] = field(default_factory=list)
    asp_syntax_query_predicates: list[SyntaxQueryPredicate] = field(
        default_factory=list
    )
    render_mode: str | None = None
    source_version: str = "worktree"
    terms: list[str] = field(default_factory=list)
    surfaces: list[str] = field(default_factory=list)
    positionals: list[str] = field(default_factory=list)


def consume_query_arg(
    state: QueryParseState,
    args: list[str] | tuple[str, ...],
    index: int,
) -> int | ProtocolArgError:
    arg = args[index]
    if arg in {"--term", "--query"}:
        return _consume_query_term(state, args, index, arg)
    if arg in {"--names-only", "--code", "--json"}:
        _set_query_flag(state, arg)
        return index + 1
    if arg == "--workspace":
        value = _optional_arg(args, index + 1)
        if value is None:
            return ProtocolArgError("--workspace requires a workspace root")
        state.workspace = True
        state.workspace_root = Path(value)
        return index + 2
    if arg == "--surface":
        value = _optional_arg(args, index + 1)
        surfaces, error = normalize_query_surfaces(value)
        if error is not None:
            return ProtocolArgError(error)
        state.surfaces.extend(surfaces)
        return index + 2
    if arg == "--view":
        value = _optional_arg(args, index + 1)
        render_mode, error = normalize_query_view(value)
        if error is not None:
            return ProtocolArgError(error)
        state.render_mode = render_mode
        return index + 2
    if arg in {
        "--selector",
        "--package",
        "--catalog",
        "--where",
        "--source",
        "--treesitter-query",
        "--asp-syntax-query-captures",
        "--asp-syntax-query-node-types",
        "--asp-syntax-query-fields",
        "--asp-syntax-query-predicates-json",
    }:
        return _consume_query_option(state, args, index, arg)
    if arg in {"--help", "-h"}:
        return ProtocolArgError(QUERY_USAGE)
    if arg.startswith("-"):
        return ProtocolArgError(f"unknown query option: {arg}")
    state.positionals.append(arg)
    return index + 1


def _consume_query_term(
    state: QueryParseState,
    args: list[str] | tuple[str, ...],
    index: int,
    arg: str,
) -> int | ProtocolArgError:
    value = _optional_arg(args, index + 1)
    if value is None:
        return ProtocolArgError(f"{arg} requires a value")
    if arg == "--query":
        state.terms.extend(term.strip() for term in value.split("|") if term.strip())
    else:
        state.terms.append(value)
    return index + 2


def _set_query_flag(state: QueryParseState, arg: str) -> None:
    if arg == "--names-only":
        state.names_only = True
    elif arg == "--code":
        state.code_only = True
    else:
        state.json_output = True


def _consume_query_option(
    state: QueryParseState,
    args: list[str] | tuple[str, ...],
    index: int,
    arg: str,
) -> int | ProtocolArgError:
    value = _optional_arg(args, index + 1)
    if value is None:
        return ProtocolArgError(f"{arg} requires {_query_option_value_name(arg)}")
    match arg:
        case "--selector":
            state.selector = value
        case "--catalog":
            state.catalog = value
        case "--where":
            state.flow_lite_where = value
        case "--source":
            source_version, error = normalize_query_source_version(value)
            if error is not None:
                return ProtocolArgError(error)
            state.source_version = source_version
        case "--treesitter-query":
            state.tree_sitter_query = value
        case "--asp-syntax-query-captures":
            state.asp_syntax_query_captures = _split_asp_syntax_query_plan_list(value)
        case "--asp-syntax-query-node-types":
            state.asp_syntax_query_node_types = _split_asp_syntax_query_plan_list(value)
        case "--asp-syntax-query-fields":
            state.asp_syntax_query_fields = _split_asp_syntax_query_plan_list(value)
        case "--asp-syntax-query-predicates-json":
            try:
                state.asp_syntax_query_predicates = parse_asp_syntax_query_predicates(
                    value
                )
            except ValueError as error:
                return ProtocolArgError(f"invalid ASP syntax query predicates: {error}")
        case _:
            state.package_path = Path(value)
    return index + 2


def _query_option_value_name(arg: str) -> str:
    return {
        "--selector": "an owner path",
        "--package": "a package path",
        "--catalog": "a catalog id",
        "--where": "flow-lite constraints",
        "--source": "worktree, index, or head",
        "--treesitter-query": "a tree-sitter query expression",
        "--asp-syntax-query-captures": "an ASP query capture list",
        "--asp-syntax-query-node-types": "an ASP query node-type list",
        "--asp-syntax-query-fields": "an ASP query field list",
        "--asp-syntax-query-predicates-json": "an ASP query predicate JSON array",
    }[arg]


def normalize_query_source_version(value: str | None) -> tuple[str, str | None]:
    if value in {"worktree", "index", "head"}:
        return value, None
    return (
        "worktree",
        f"unknown query --source value: {value}; expected worktree, index, or head",
    )


def _split_asp_syntax_query_plan_list(value: str) -> list[str]:
    return sorted({item.strip() for item in value.split(",") if item.strip()})


def _optional_arg(args: list[str] | tuple[str, ...], index: int) -> str | None:
    if index >= len(args):
        return None
    value = args[index]
    if value.startswith("-"):
        return None
    return value
