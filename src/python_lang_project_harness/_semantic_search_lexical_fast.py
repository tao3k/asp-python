"""Fast compact frontiers for Python lexical seed views."""

from __future__ import annotations

from pathlib import Path

from ._cli_args import ProtocolArgs
from ._semantic_search_prefilter import prefilter_python_text_search_paths


def render_fast_lexical_seed_search(
    args: ProtocolArgs, project_root: Path
) -> str | None:
    """Render lexical owner seeds without parsing candidate modules."""

    if not _supports_fast_lexical_seed_search(args):
        return None
    query_terms = _fast_lexical_query_terms(args)
    prefilter = prefilter_python_text_search_paths(
        project_root,
        query_terms,
        owner_path=args.owner_path,
    )
    if prefilter is None or not prefilter.paths:
        return None
    owners = tuple(_relative_owner_path(path, project_root) for path in prefilter.paths)
    return _render_fast_lexical_seed_text(query_terms, owners, prefilter.runtime_cost())


def _supports_fast_lexical_seed_search(args: ProtocolArgs) -> bool:
    return (
        args.command == "search"
        and args.view == "lexical"
        and args.render_mode == "seeds"
        and not args.json
        and not args.code_only
        and bool(_fast_lexical_query_terms(args))
        and args.pipes in {("owner",), ("owner", "tests")}
        and args.item_query is None
        and args.dependency is None
    )


def _fast_lexical_query_terms(args: ProtocolArgs) -> tuple[str, ...]:
    if args.query_set:
        return args.query_set
    if args.query:
        return (args.query,)
    return ()


def _relative_owner_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _render_fast_lexical_seed_text(
    query_terms: tuple[str, ...],
    owners: tuple[str, ...],
    runtime_cost: dict[str, object],
) -> str:
    query = ",".join(query_terms)
    declarations = [f"Q=query:term({query})!lexical"]
    edges = ["Q:matches"]
    rank = ["Q"]
    for index, owner in enumerate(owners, start=1):
        suffix = "" if index == 1 else str(index)
        owner_id = f"O{suffix}"
        test_id = f"T{suffix}"
        declarations.append(f"{owner_id}=owner:path({owner})!owner")
        declarations.append(f"{test_id}=test:path({owner})!tests")
        edges.extend((f"{owner_id}:selects", f"{test_id}:covers"))
        rank.extend((owner_id, test_id))
    return "\n".join(
        [
            (
                f"[search-lexical] q={query} querySet={len(query_terms)} "
                "selector=lexical-set view=hits alg=query-set-owner-resolution"
            ),
            "legend: ID=kind:role(value)!next; edge SRC>{DST:rel}; frontier ID.next",
            "aliases: graph:{G=search,Q=query,O=owner,T=test}",
            ";".join(declarations),
            f"G>{{{','.join(edges)}}}",
            f"rank={','.join(rank)} frontier={_frontier(rank)}",
            "entries=owner-query(O,Q=>items+tests+dependency-usage),owner-tests(O=>covering-tests+test-entrypoints+fixtures)",
            f'|note kind=runtime-prefilter message="{runtime_cost["reason"]}"',
            "",
        ]
    )


def _frontier(rank: list[str]) -> str:
    return ",".join(f"{item}.{_frontier_kind(item)}" for item in rank)


def _frontier_kind(item: str) -> str:
    if item == "Q":
        return "lexical"
    if item.startswith("T"):
        return "tests"
    return "owner"
