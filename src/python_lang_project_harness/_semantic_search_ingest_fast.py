"""Fast empty-stdin guidance for Python search ingest seed view."""

from __future__ import annotations

from pathlib import Path

from ._cli_args import ProtocolArgs

_STDIN_REQUIRED_NOTE = (
    '|note kind=stdin-required message="search ingest consumes stdin candidate '
    'paths; use search prime --view seeds for project discovery"'
)
_EMPTY_STDIN_NEXT = (
    '|next prime:"search prime --view seeds"(scope=project-discovery),'
    'ingest:"pipe candidate paths into search ingest items tests --view seeds"'
    "(scope=stdin-candidates)"
)


def render_fast_empty_ingest_search(
    args: ProtocolArgs,
    project_root: Path,
    stdin: str,
) -> str | None:
    """Render empty ingest seed guidance without running the full harness."""

    del project_root
    if not _supports_fast_empty_ingest(args, stdin):
        return None
    return _render_fast_empty_ingest_seed_text(args)


def _supports_fast_empty_ingest(args: ProtocolArgs, stdin: str) -> bool:
    return (
        args.command == "search"
        and args.view == "ingest"
        and args.render_mode == "seeds"
        and not args.json
        and stdin == ""
        and args.query is None
        and args.item_query is None
        and args.owner_path is None
        and not args.query_set
    )


def _render_fast_empty_ingest_seed_text(args: ProtocolArgs) -> str:
    root = args.project_root.as_posix() if args.project_root is not None else "."
    lines = [
        f"[search-ingest] root={root or '.'} alg=seed-frontier",
        "legend: ID=kind:role(value)!next; edge SRC>{DST:rel}; frontier ID.next",
        "aliases: graph:{G=search}",
        "G>{}",
        "rank= frontier=",
        _STDIN_REQUIRED_NOTE,
        _EMPTY_STDIN_NEXT,
    ]
    return "\n".join(lines) + "\n"
