"""Execute provider-native Python query protocol commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

from ._semantic_search_item_lines import owner_item_query_lines
from ._semantic_search_items import owner_item_semantic_query_packet
from ._semantic_selector_identity import python_structural_selector_owner_path

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

    if args.selector is None and (args.owner_path is not None or args.terms):
        raise ValueError(
            "python query requires an exact --selector; use `asp python search owner "
            "<owner-path> items --query <symbol> --names-only --workspace .` for discovery"
        )
    if args.code_only and not _selector_is_structural(args.selector):
        raise ValueError(
            "query requires parser-owned structural selector identity; "
            "status=selector-not-materialized "
            "reason=non-structural-selector "
            "nextAction=refresh-parser-projection"
        )
    if _selector_looks_like_source_locator_hint(args.selector):
        raise ValueError(
            "query requires parser-owned selector identity; "
            "source locator hints are not executable selectors"
        )

    owner_path = args.owner_path or _selector_owner_path(args.selector) or ""
    item_query = "|".join(args.query_set)
    _write_item_query_response(
        args, report, project_root, stdout, owner_path, item_query
    )
    return 0


def _write_item_query_response(
    args: ProtocolArgs,
    report: Any,
    project_root: Path,
    stdout: TextIO,
    owner_path: str,
    item_query: str,
) -> None:
    packet = owner_item_semantic_query_packet(
        report,
        project_root,
        owner_path,
        item_query,
        output_mode="names" if args.names_only else "code",
        selector=args.selector,
    )
    if args.json:
        stdout.write(json.dumps(packet, separators=(",", ":")))
    elif args.code_only:
        stdout.write(
            "\n".join(
                str(match["code"])
                for match in packet["matches"]
                if isinstance(match.get("code"), str)
            )
        )
    else:
        stdout.write(
            owner_item_query_lines(
                report,
                project_root,
                owner_path,
                item_query,
                names_only=args.names_only,
            )
        )
    stdout.write("\n")


def _selector_is_structural(selector: str | None) -> bool:
    if selector is None:
        return False
    normalized = selector.strip()
    return normalized.startswith("python://") and "#item/" in normalized


def _selector_owner_path(selector: str | None) -> str | None:
    return python_structural_selector_owner_path(selector)


def _selector_looks_like_source_locator_hint(selector: str | None) -> bool:
    if selector is None:
        return False
    normalized = selector.replace("\\", "/").removeprefix("owner:")
    if any(marker in normalized for marker in ("*", "{", "}")):
        return False
    return ".py:" in normalized
