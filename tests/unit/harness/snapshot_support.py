"""Snapshot assertion helpers for harness policy and renderer tests."""

from __future__ import annotations

import os
from pathlib import Path

SNAPSHOT_ROOT = Path(__file__).parent.parent / "snapshots"
UPDATE_ENV_VAR = "ASP_PYTHON_UPDATE_SNAPSHOTS"


def assert_snapshot(
    snapshot_name: str,
    rendered: str,
    *,
    source: str | None = None,
) -> None:
    snapshot_path = SNAPSHOT_ROOT / f"{snapshot_name}.snap"
    if os.environ.get(UPDATE_ENV_VAR) == "1":
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            _snapshot_text(rendered, source=source),
            encoding="utf-8",
        )
        return

    expected = _snapshot_body(snapshot_path.read_text(encoding="utf-8"))
    assert rendered == expected


def normalize_temp_root(rendered: str, root: Path) -> str:
    root_text = str(root)
    return rendered.replace(root_text, "$TEMP").replace(
        root_text.replace("\\", "/"),
        "$TEMP",
    )


def _snapshot_text(rendered: str, *, source: str | None) -> str:
    if source is None:
        return rendered
    return f"---\nsource: {source}\nexpression: rendered\n---\n{rendered}"


def _snapshot_body(snapshot_text: str) -> str:
    if not snapshot_text.startswith("---\n"):
        return snapshot_text
    parts = snapshot_text.split("---\n", 2)
    return parts[2]
