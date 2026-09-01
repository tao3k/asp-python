"""Subprocess helpers for semantic-search prefilter tools."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_prefilter_command(
    command: list[str],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Run one bounded filesystem prefilter command."""

    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, "", "")
