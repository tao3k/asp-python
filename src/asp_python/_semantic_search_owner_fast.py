"""Fast compact frontiers for Python exact-owner seed view."""

from __future__ import annotations

from pathlib import Path

from ._cli_args import ProtocolArgs


def render_fast_owner_seed_search(args: ProtocolArgs, project_root: Path) -> str | None:
    """Render exact owner seeds without parsing the owner file."""

    owner_path = _fast_owner_path(args, project_root)
    if owner_path is None:
        return None
    owner = _relative_owner_path(owner_path, project_root)
    return "\n".join(
        [
            f"[search-owner] q={owner} alg=fast-exact-owner-frontier",
            "legend: ID=kind:role(value)!next; edge SRC>{DST:rel}; frontier ID.next",
            "aliases: graph:{G=search,O=owner,T=test}",
            f"O=owner:path({owner})!owner;T=test:path({owner})!tests",
            "G>{O:selects,T:covers}",
            "rank=O,T frontier=O.owner,T.tests",
            "entries=owner-tests(O=>covering-tests+test-entrypoints+fixtures)",
            "",
        ]
    )


def _fast_owner_path(args: ProtocolArgs, project_root: Path) -> Path | None:
    if (
        args.command != "search"
        or args.view != "owner"
        or args.render_mode != "seeds"
        or args.json
        or args.query is None
        or args.item_query is not None
        or args.owner_path is not None
        or args.query_set
        or args.pipes
    ):
        return None
    raw_path = Path(args.query)
    owner_path = raw_path if raw_path.is_absolute() else project_root / raw_path
    try:
        resolved_root = project_root.resolve()
        resolved_owner = owner_path.resolve()
        resolved_owner.relative_to(resolved_root)
    except (OSError, ValueError):
        return None
    if not resolved_owner.is_file() or resolved_owner.suffix != ".py":
        return None
    return resolved_owner


def _relative_owner_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
