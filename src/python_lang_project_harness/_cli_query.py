"""Execute provider-native Python query protocol commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from ._cli_args import ProtocolArgs


def run_query_command(
    args: ProtocolArgs,
    *,
    report: Any,
    project_root: Path,
    stdout: TextIO,
) -> int:
    """Run a parsed query command against parser-owned report facts."""

    if args.catalog == "flow-lite":
        from ._flow_lite_query import write_flow_lite_query_response

        write_flow_lite_query_response(
            args,
            project_root=project_root,
            stdout=stdout,
        )
        return 0

    if args.catalog is not None or args.tree_sitter_query is not None:
        from ._tree_sitter_query import write_tree_sitter_query_response

        write_tree_sitter_query_response(
            args,
            report=report,
            project_root=project_root,
            stdout=stdout,
        )
        return 0

    raise ValueError(
        "exact source projection is ASP-owned; use `asp python query "
        "--selector <exact-structural-selector> --projection "
        "source|callable-skeleton --workspace <workspace-root>`"
    )
