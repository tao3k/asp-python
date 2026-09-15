"""Flow-lite query compatibility output for the Python provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from ._flow_lite_query_packet import (
    _flow_lite_frontier,
    _flow_lite_packet,
    _parse_flow_lite_where,
)

if TYPE_CHECKING:
    from ._cli_args import ProtocolArgs


def write_flow_lite_query_response(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
) -> None:
    """Write compact or JSON semantic-flow-lite output."""

    where = _parse_flow_lite_where(args.flow_lite_where or "")
    if args.json:
        stdout.write(
            json.dumps(
                _flow_lite_packet(project_root, where),
                separators=(",", ":"),
            )
        )
        stdout.write("\n")
        return
    stdout.write(_flow_lite_frontier(project_root, where))
    stdout.write("\n")
