"""Stdin ingest helpers for Python semantic search."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import location

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts


def ingest_hits(
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    stdin: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Detect stdin shape and return owner-grouped hits."""

    detection, records = detect_ingest_records(stdin)
    owner_paths = {
        _display_path(node.path, project_root) for node in facts.nodes if node.is_valid
    }
    hits: list[dict[str, Any]] = []
    for record in records:
        owner_path = ingest_owner_path(record["path"], owner_paths)
        hits.append(
            {
                "kind": "text",
                "ownerPath": owner_path,
                "location": location(record["path"], record.get("line")),
                "score": 2,
                "reason": f"ingest-{detection['source']}",
                "snippet": record.get("text", ""),
                "fields": {"source": "ingest"},
            }
        )
    return detection, hits


def detect_ingest_records(stdin: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Detect rg/vimgrep/path-list stdin shapes."""

    byte_count = len(stdin.encode())
    line_count = (
        0 if not stdin else stdin.count("\n") + (0 if stdin.endswith("\n") else 1)
    )
    source = "unknown"
    records: list[dict[str, Any]] = []
    if "\0" in stdin:
        source = "path-list-nul"
        records = [{"path": path} for path in stdin.split("\0") if path]
    else:
        lines = [line for line in stdin.splitlines() if line.strip()]
        if lines and all(looks_like_path(line) for line in lines):
            source = "path-list"
            records = [{"path": line.strip()} for line in lines]
        else:
            parsed = [parse_rg_line(line) for line in lines]
            records = [record for record in parsed if record is not None]
            if records:
                source = (
                    "vimgrep"
                    if any("column" in record for record in records)
                    else "rg-n"
                )
            elif lines and all(line.lstrip().startswith("{") for line in lines[:3]):
                source = "rg-json"
    sample = {"sample": stdin[:160]} if stdin else {}
    return {
        "source": source,
        "lineCount": line_count,
        "byteCount": byte_count,
        **sample,
    }, records


def parse_rg_line(line: str) -> dict[str, Any] | None:
    """Parse `rg -n` or vimgrep-like output."""

    match = re.match(
        r"^(?P<path>.*?):(?P<line>\d+)(?::(?P<column>\d+))?:(?P<text>.*)$", line
    )
    if match is None:
        return None
    return {
        "path": match.group("path"),
        "line": int(match.group("line")),
        **(
            {"column": int(match.group("column"))}
            if match.group("column") is not None
            else {}
        ),
        "text": match.group("text").strip(),
    }


def looks_like_path(line: str) -> bool:
    """Return whether a line looks like a plain path list entry."""

    stripped = line.strip()
    return (
        stripped.endswith(".py") or os.sep in stripped or stripped.startswith(".")
    ) and ":" not in stripped


def ingest_owner_path(path: str, owner_paths: set[str]) -> str:
    """Map an ingested path back to a parser-visible owner when possible."""

    normalized = path.removeprefix("./")
    if normalized in owner_paths:
        return normalized
    matches = sorted(
        (
            owner_path
            for owner_path in owner_paths
            if normalized == owner_path
            or normalized.startswith(owner_path.rstrip("/") + "/")
        ),
        key=len,
        reverse=True,
    )
    return matches[0] if matches else normalized


def _display_path(path: str, project_root: Path) -> str:
    from ._semantic_search_common import semantic_search_display_path

    return semantic_search_display_path(path, project_root)
