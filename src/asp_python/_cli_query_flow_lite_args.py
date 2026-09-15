"""Flow-lite query argument helpers for the Python CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_FLOW_LITE_CATALOG_ID = "flow-lite"


def is_flow_lite_query_state(state: Any) -> bool:
    return state.catalog == _FLOW_LITE_CATALOG_ID


def flow_lite_query_args_error(state: Any) -> str | None:
    if state.tree_sitter_query is not None:
        return "query --catalog flow-lite cannot be combined with --treesitter-query"
    if state.workspace_root is not None and state.positionals:
        return (
            "query accepts either --workspace <workspace-root> or one positional "
            "WORKSPACE, not both"
        )
    if len(state.positionals) > 1:
        return "query accepts at most one positional WORKSPACE"
    if state.surfaces:
        return "query --surface cannot be combined with --catalog flow-lite"
    if state.render_mode is not None:
        return "query --view cannot be combined with --catalog flow-lite"
    if state.flow_lite_where is None:
        return "query --catalog flow-lite requires --where"
    return flow_lite_where_error(state.flow_lite_where)


def flow_lite_query_protocol_args(args_type: type[Any], state: Any) -> Any:
    return args_type(
        "query",
        catalog=state.catalog,
        flow_lite_where=state.flow_lite_where,
        project_root=_flow_lite_query_project_root(state),
        package_path=state.package_path,
        workspace=state.workspace or bool(state.positionals),
        json=state.json_output,
    )


def _flow_lite_query_project_root(state: Any) -> Path | None:
    if state.workspace_root is not None:
        return state.workspace_root
    if len(state.positionals) == 1:
        return Path(state.positionals[0])
    return None


def flow_lite_where_error(value: str) -> str | None:
    seen: set[str] = set()
    required = {"source.call", "sink.constructs", "scope.fn"}
    for constraint in value.split():
        key, separator, raw_value = constraint.partition("=")
        if not separator:
            return f"invalid flow-lite --where constraint `{constraint}`"
        if not raw_value.strip():
            return f"flow-lite --where key `{key}` has an empty value"
        if key not in required:
            return (
                f"unsupported flow-lite --where key `{key}`; supported keys are "
                "source.call,sink.constructs,scope.fn"
            )
        if key in seen:
            return f"duplicate flow-lite --where key `{key}`"
        seen.add(key)
    for key in ("source.call", "sink.constructs", "scope.fn"):
        if key not in seen:
            return f"flow-lite --where requires {key}"
    return None
