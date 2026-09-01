"""Small helpers shared by Python semantic-search modules."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._render import _render_display_path
from ._semantic_search_model import Fields, FieldValue

if TYPE_CHECKING:
    from collections.abc import Iterable

    from python_lang_parser import SourceLocation


def semantic_search_display_path(path: str | Path, project_root: Path) -> str:
    """Return an agent-facing path relative to the project root when possible."""

    return _render_display_path(path, project_root=project_root)


def location(
    path: str,
    line: int | None = None,
    column: int | None = None,
) -> dict[str, Any]:
    """Return a schema-compatible semantic-search location."""

    payload: dict[str, Any] = {"path": path}
    if line is not None and line > 0:
        payload["line"] = line
    if column is not None:
        payload["column"] = max(1, column)
    return payload


def location_from_source(
    source_location: SourceLocation,
    project_root: Path,
) -> dict[str, Any]:
    """Return a packet location from a parser source location."""

    return location(
        semantic_search_display_path(source_location.path or ".", project_root),
        source_location.line,
        source_location.column,
    )


def header(view: str, fields: Fields) -> dict[str, Any]:
    """Return a semantic-search packet header."""

    return {"kind": f"search-{view}", "fields": compact_fields(fields)}


def compact_fields(fields: Fields) -> Fields:
    """Drop empty fields from compact and JSON payloads."""

    return {
        key: value
        for key, value in fields.items()
        if value is not None and value != [] and value != ""
    }


def dedupe(values: Iterable[str]) -> list[str]:
    """Return values in first-seen order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def path_hit(
    owner_path: str,
    path: str,
    *,
    kind: str = "path",
    symbol: str | None = None,
    score: int = 2,
    reason: str = "path",
    fields: Fields | None = None,
) -> dict[str, Any]:
    """Return a simple path-like search hit."""

    hit: dict[str, Any] = {
        "kind": kind,
        "ownerPath": owner_path,
        "location": {"path": path},
        "score": score,
        "reason": reason,
    }
    if symbol is not None:
        hit["symbol"] = symbol
    if fields:
        hit["fields"] = fields
    return hit


def dedupe_hits(hits: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return deterministic unique hits."""

    seen: set[tuple[str, str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for hit in hits:
        key = (
            hit["kind"],
            hit["ownerPath"],
            hit.get("symbol", ""),
            json.dumps(hit["location"], sort_keys=True),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(hit)
    return sorted(
        result, key=lambda hit: (-hit["score"], hit["ownerPath"], hit["kind"])
    )


def render_fields(fields: Fields) -> str:
    """Render compact `key=value` fields."""

    return " ".join(
        f"{key}={escape_field_value(value)}"
        for key, value in fields.items()
        if value != [] and value != ""
    )


def escape_field_value(value: FieldValue) -> str:
    """Render one compact field value."""

    if isinstance(value, list):
        return ",".join(escape_scalar(item) for item in value)
    return escape_scalar(value)


def escape_scalar(value: str | int | float | bool) -> str:
    """Render one compact scalar."""

    text = str(value).lower() if isinstance(value, bool) else str(value)
    if re.search(r"[\s,=]", text):
        return json.dumps(text)
    return text


def render_location(search_location: dict[str, Any]) -> str:
    """Render a compact location."""

    fields: Fields = {"path": search_location["path"]}
    if "line" in search_location and "column" in search_location:
        fields["line"] = search_location["line"]
        fields["column"] = search_location["column"]
        return render_fields(fields)
    if "line" in search_location:
        fields["line"] = search_location["line"]
    elif "lineRange" in search_location:
        line_range = str(search_location["lineRange"])
        start, _, end = line_range.partition(":")
        fields["line"] = start if start and (not end or start == end) else line_range
    return render_fields(fields)
