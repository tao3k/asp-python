"""CLI parsing helpers for Python semantic-search commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ._semantic_language import python_semantic_search_view_descriptor


@dataclass(slots=True)
class ParsedSemanticSearchArgs:
    view: str | None = None
    query: str | None = None
    item_query: str | None = None
    project_root: Path | None = None
    package_path: Path | None = None
    workspace: bool = False
    owner_path: str | None = None
    dependency: str | None = None
    query_set: tuple[str, ...] = ()
    pipes: tuple[str, ...] = ()
    json: bool = False
    render_mode: str | None = None
    error: str | None = None


@dataclass(slots=True)
class _SearchOptionState:
    positionals: list[str] = field(default_factory=list)
    query_set: list[str] = field(default_factory=list)
    item_query: str | None = None
    json: bool = False
    render_mode: str | None = None
    package_path: Path | None = None
    workspace: bool = False
    workspace_root: Path | None = None
    owner_path: str | None = None
    dependency: str | None = None


@dataclass(slots=True)
class _ConsumedOption:
    advance: int = 1
    error: str | None = None


def parse_semantic_search_args(
    args: list[str] | tuple[str, ...],
) -> ParsedSemanticSearchArgs:
    view, descriptor, error = _search_view_descriptor(args)
    if error is not None or view is None or descriptor is None:
        return ParsedSemanticSearchArgs(error=error)
    state, error = _parse_search_option_state(view, args[1:])
    if error is not None:
        return ParsedSemanticSearchArgs(error=error)
    error = _validate_search_option_state(view, state)
    if error is not None:
        return ParsedSemanticSearchArgs(error=error)
    return _search_args_for_descriptor(view, descriptor, state)


def _search_view_descriptor(
    args: list[str] | tuple[str, ...],
) -> tuple[str | None, dict[str, object] | None, str | None]:
    view = args[0] if args else None
    if view is None or view in {"--help", "-h"}:
        return None, None, _semantic_search_usage()
    descriptor = python_semantic_search_view_descriptor(view)
    if descriptor is None:
        return view, None, f"unknown search view: {view}"
    return view, descriptor, None


def _semantic_search_usage() -> str:
    return (
        "usage: asp-python search "
        "<workspace|prime|owner|dependency|deps|api|public-external-types|policy|symbol|callsite|import|tests|lexical|reasoning|env|runtime-source|lang|std|capability|extension|pattern|compare|text|ingest|semantic-facts> "
        "... [--json] [--package PATH] [--workspace <workspace-root>]; "
        "dependency/deps are manifest-first, import-usage backed, and cache hashes not raw source"
    )


def _validate_search_option_state(
    view: str,
    state: _SearchOptionState,
) -> str | None:
    if state.query_set and not _search_view_supports_query_bundle(view):
        return f"search {view} does not support repeated --query"
    if state.item_query is not None and view not in {"owner", "reasoning"}:
        return "--query is only supported by search owner items"
    if state.owner_path is not None and view not in {"lexical", "reasoning"}:
        return "--owner is only supported by search lexical or reasoning"
    if state.dependency is not None and view != "reasoning":
        return "--dependency is only supported by search reasoning"
    return None


def _search_args_for_descriptor(
    view: str,
    descriptor: dict[str, object],
    state: _SearchOptionState,
) -> ParsedSemanticSearchArgs:
    accepted_pipes = descriptor.get("acceptedPipes", ())
    normalized_pipes = (
        accepted_pipes if isinstance(accepted_pipes, tuple | list) else ()
    )
    if view == "lexical":
        return _optional_query_args(view, state, normalized_pipes)
    if descriptor["requiresQuery"]:
        return _required_query_args(view, descriptor, state)
    return _project_only_args(view, descriptor, state)


def _parse_search_option_state(
    view: str,
    args: list[str] | tuple[str, ...],
) -> tuple[_SearchOptionState, str | None]:
    state = _SearchOptionState()
    index = 0
    while index < len(args):
        consumed = _consume_search_option(view, args, index, state)
        if consumed.error is not None:
            return state, consumed.error
        index += consumed.advance
    return state, None


def _consume_search_option(
    view: str,
    args: list[str] | tuple[str, ...],
    index: int,
    state: _SearchOptionState,
) -> _ConsumedOption:
    arg = args[index]
    if _is_flag_like_literal_search_query(
        view, state.positionals, state.query_set, arg
    ):
        state.positionals.append(arg)
        return _ConsumedOption()

    match arg:
        case "--json":
            state.json = True
        case "--view":
            value = _optional_arg(args, index + 1)
            if value not in {"graph", "hits", "both", "seeds"}:
                return _ConsumedOption(
                    error="--view requires graph, hits, both, or seeds",
                )
            state.render_mode = value
            return _ConsumedOption(advance=2)
        case "--package":
            value = _optional_arg(args, index + 1)
            if value is None:
                return _ConsumedOption(error="--package requires a package path")
            state.package_path = Path(value)
            return _ConsumedOption(advance=2)
        case "--workspace":
            value = _optional_arg(args, index + 1)
            if value is None:
                return _ConsumedOption(error="--workspace requires a workspace root")
            state.workspace = True
            state.workspace_root = Path(value)
            return _ConsumedOption(advance=2)
        case "--owner":
            value = _literal_arg(args, index + 1)
            if value is None:
                return _ConsumedOption(error="--owner requires an owner path")
            state.owner_path = value
            return _ConsumedOption(advance=2)
        case "--dependency":
            value = _literal_arg(args, index + 1)
            if value is None:
                return _ConsumedOption(error="--dependency requires a dependency")
            state.dependency = value
            return _ConsumedOption(advance=2)
        case "--query":
            value = _literal_arg(args, index + 1)
            if value is None:
                return _ConsumedOption(error="--query requires a query term")
            if view == "lexical":
                state.query_set.append(value)
                return _ConsumedOption(advance=2)
            state.item_query = value
            return _ConsumedOption(advance=2)
        case _ if arg.startswith("-"):
            return _ConsumedOption(error=f"unknown search option: {arg}")
        case _:
            state.positionals.append(arg)
    return _ConsumedOption()


def _required_query_args(
    view: str,
    descriptor: dict[str, object],
    state: _SearchOptionState,
) -> ParsedSemanticSearchArgs:
    if _search_view_accepts_optional_terms(view):
        return _required_term_query_args(view, state)

    query = (
        ",".join(state.query_set)
        if state.query_set
        else (state.positionals[0] if state.positionals else None)
    )
    if query is None:
        return ParsedSemanticSearchArgs(error=f"search {view} requires a query")

    accepted_pipes = descriptor.get("acceptedPipes", ())
    pipes, project_root, error = _parse_search_pipe_positionals(
        state.positionals if state.query_set else state.positionals[1:],
        accepted_pipes if isinstance(accepted_pipes, tuple | list) else (),
    )
    if error is not None:
        return ParsedSemanticSearchArgs(error=error)
    if project_root is not None:
        return ParsedSemanticSearchArgs(
            error="search does not accept positional WORKSPACE; use --workspace <workspace-root>",
        )
    project_root = (
        str(state.workspace_root) if state.workspace_root is not None else None
    )
    return ParsedSemanticSearchArgs(
        view=view,
        query=query,
        item_query=state.item_query,
        owner_path=state.owner_path,
        dependency=state.dependency,
        query_set=tuple(state.query_set),
        project_root=None if project_root is None else Path(project_root),
        package_path=state.package_path,
        workspace=state.workspace,
        pipes=tuple(pipes),
        json=state.json,
        render_mode=state.render_mode,
    )


def _required_term_query_args(
    view: str,
    state: _SearchOptionState,
) -> ParsedSemanticSearchArgs:
    query = " ".join(state.positionals)
    if not query:
        return ParsedSemanticSearchArgs(error=f"search {view} requires a query")
    project_root = (
        str(state.workspace_root) if state.workspace_root is not None else None
    )
    return ParsedSemanticSearchArgs(
        view=view,
        query=query,
        item_query=state.item_query,
        owner_path=state.owner_path,
        dependency=state.dependency,
        query_set=tuple(state.query_set),
        project_root=None if project_root is None else Path(project_root),
        package_path=state.package_path,
        workspace=state.workspace,
        json=state.json,
        render_mode=state.render_mode,
    )


def _project_only_args(
    view: str,
    descriptor: dict[str, object],
    state: _SearchOptionState,
) -> ParsedSemanticSearchArgs:
    accepted_pipes = descriptor.get("acceptedPipes", ())
    normalized_pipes = (
        accepted_pipes if isinstance(accepted_pipes, tuple | list) else ()
    )
    if _search_view_accepts_optional_terms(view):
        return _optional_query_args(
            view,
            state,
            normalized_pipes,
        )
    pipes, project_root, error = _parse_search_pipe_positionals(
        state.positionals,
        normalized_pipes,
    )
    if error is not None:
        return ParsedSemanticSearchArgs(error=error)
    if project_root is not None:
        return ParsedSemanticSearchArgs(
            error="search does not accept positional WORKSPACE; use --workspace <workspace-root>",
        )
    project_root = (
        str(state.workspace_root) if state.workspace_root is not None else None
    )
    return ParsedSemanticSearchArgs(
        view=view,
        project_root=None if project_root is None else Path(project_root),
        package_path=state.package_path,
        workspace=state.workspace,
        pipes=tuple(pipes),
        json=state.json,
        render_mode=state.render_mode,
    )


def _optional_query_args(
    view: str,
    state: _SearchOptionState,
    accepted_pipes: list[str] | tuple[str, ...],
) -> ParsedSemanticSearchArgs:
    if view == "lexical":
        if state.query_set:
            query = ",".join(state.query_set)
            positionals = state.positionals
        elif state.positionals:
            query = state.positionals[0]
            positionals = state.positionals[1:]
        else:
            query = None
            positionals = []
        pipes, project_root, error = _parse_search_pipe_positionals(
            positionals,
            accepted_pipes,
        )
        if error is not None:
            return ParsedSemanticSearchArgs(error=error)
        if project_root is not None:
            return ParsedSemanticSearchArgs(
                error="search does not accept positional WORKSPACE; use --workspace <workspace-root>",
            )
        project_root = (
            str(state.workspace_root) if state.workspace_root is not None else None
        )
        return ParsedSemanticSearchArgs(
            view=view,
            query=query,
            owner_path=state.owner_path,
            project_root=None if project_root is None else Path(project_root),
            package_path=state.package_path,
            workspace=state.workspace,
            query_set=tuple(state.query_set),
            pipes=tuple(pipes),
            json=state.json,
            render_mode=state.render_mode,
        )
    project_root = (
        str(state.workspace_root) if state.workspace_root is not None else None
    )
    return ParsedSemanticSearchArgs(
        view=view,
        query=" ".join(state.positionals) if state.positionals else None,
        project_root=None if project_root is None else Path(project_root),
        package_path=state.package_path,
        workspace=state.workspace,
        json=state.json,
        render_mode=state.render_mode,
    )


def _parse_search_pipe_positionals(
    positionals: list[str],
    accepted_pipes: list[str] | tuple[str, ...],
) -> tuple[list[str], str | None, str | None]:
    pipes: list[str] = []
    index = 0
    while index < len(positionals) and index < len(accepted_pipes):
        if positionals[index] != accepted_pipes[index]:
            break
        pipes.append(positionals[index])
        index += 1
    remaining = positionals[index:]
    if len(remaining) > 1:
        looks_like_out_of_order_pipe = (
            index < len(accepted_pipes) and remaining[0] in accepted_pipes
        )
        if not accepted_pipes or not looks_like_out_of_order_pipe:
            return (
                pipes,
                remaining[0],
                "search does not accept positional WORKSPACE; use --workspace <workspace-root>",
            )
        return (
            pipes,
            remaining[0],
            f"expected pipes ({','.join(accepted_pipes)}) before workspace selector",
        )
    return pipes, (remaining[0] if remaining else None), None


def _optional_arg(args: list[str] | tuple[str, ...], index: int) -> str | None:
    if index >= len(args):
        return None
    value = args[index]
    if value.startswith("-"):
        return None
    return value


def _literal_arg(args: list[str] | tuple[str, ...], index: int) -> str | None:
    return None if index >= len(args) else args[index]


def _is_flag_like_literal_search_query(
    view: str,
    positionals: list[str],
    query_set: list[str],
    arg: str,
) -> bool:
    return (
        view == "lexical"
        and not positionals
        and not query_set
        and arg.startswith("-")
        and not arg.startswith("--")
        and arg != "-h"
    )


def _search_view_supports_query_bundle(view: str) -> bool:
    return view == "lexical"


def _search_view_accepts_optional_terms(view: str) -> bool:
    return view in {
        "env",
        "runtime-source",
        "lang",
        "std",
        "capability",
        "extension",
        "pattern",
        "compare",
        "lexical",
    }
