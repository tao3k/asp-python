"""Compact and JSON renderers for Python semantic-search packets."""

from __future__ import annotations

import json
from typing import Any

from ._semantic_search_render_compact import render_compact_packet


def render_python_semantic_search_packet_json(packet: dict[str, Any]) -> str:
    """Render a semantic-search packet as compact JSON."""

    return json.dumps(packet, separators=(",", ":"), sort_keys=False) + "\n"


def render_python_semantic_search_packet(packet: dict[str, Any]) -> str:
    """Render a compact line-oriented semantic-search packet."""

    return render_compact_packet(packet)
