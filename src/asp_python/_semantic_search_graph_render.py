"""Delegate Python compact graph rendering to the shared protocol binary."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from typing import Any

from ._semantic_search_common import escape_field_value
from ._semantic_search_render_lines import render_next_action

DEFAULT_GRAPH_SEED_LIMIT = 8
SEMANTIC_AGENT_PROTOCOL_BIN_ENV = "SEMANTIC_AGENT_PROTOCOL_BIN"
GRAPH_NATIVE_NEXT_ACTION_KINDS = frozenset({"owner", "tests"})


class CompactGraphRenderError(RuntimeError):
    """Raised when the shared compact graph renderer cannot produce output."""


def compact_graph_seed_packet_text(
    packet: dict[str, Any],
    render_fields: Callable[[dict[str, Any]], str],
) -> str:
    del render_fields
    rendered = render_compact_graph_packet(
        graph_render_packet(packet),
        seed_limit=DEFAULT_GRAPH_SEED_LIMIT,
    )
    flow_lines = compact_graph_flow_lines(packet)
    if not flow_lines:
        return rendered
    return f"{rendered.rstrip()}\n" + "\n".join(flow_lines) + "\n"


def graph_render_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Return the packet projection expected by the graph-only renderer."""

    next_actions = [
        action
        for action in packet.get("nextActions", [])
        if action.get("kind") in GRAPH_NATIVE_NEXT_ACTION_KINDS
    ]
    if len(next_actions) == len(packet.get("nextActions", [])):
        return packet
    return {**packet, "nextActions": next_actions}


def compact_graph_flow_lines(packet: dict[str, Any]) -> list[str]:
    """Render non-graph flow hints after compact graph output."""

    lines = [
        f"|note kind={note['kind']} message={escape_field_value(note['message'])}"
        for note in packet.get("notes", [])
    ]
    non_graph_actions = [
        action
        for action in packet.get("nextActions", [])
        if action.get("kind") not in GRAPH_NATIVE_NEXT_ACTION_KINDS
    ]
    if non_graph_actions:
        lines.append(
            "|next "
            + ",".join(render_next_action(action) for action in non_graph_actions)
        )
    return lines


def render_compact_graph_packet(
    packet: dict[str, Any],
    *,
    seed_limit: int = DEFAULT_GRAPH_SEED_LIMIT,
) -> str:
    command = [
        os.environ.get(SEMANTIC_AGENT_PROTOCOL_BIN_ENV, "asp"),
        "graph",
        "render",
        "--packet",
        "-",
        "--view",
        "seeds",
        "--seeds",
        str(seed_limit),
    ]
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(packet, separators=(",", ":")),
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise CompactGraphRenderError(
            "asp graph renderer not found; "
            f"set {SEMANTIC_AGENT_PROTOCOL_BIN_ENV} or install "
            "asp on PATH"
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        raise CompactGraphRenderError(
            f"asp graph render failed with exit code {exc.returncode}{detail}"
        ) from exc
    return completed.stdout
