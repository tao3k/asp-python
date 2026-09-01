"""Semantic agent CLI tests for the Python harness provider."""

from __future__ import annotations

import io
from pathlib import Path

from asp_python import run_cli


def test_cli_agent_install_reports_root_asp_owner(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(
        ["agent", "install", "--client", "codex", str(tmp_path)],
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 2
    assert stdout.getvalue() == ""
    assert "asp-python agent install moved to asp" in stderr.getvalue()
    assert "asp hook install --client codex" in stderr.getvalue()


def test_cli_agent_hook_reports_root_asp_owner(
    tmp_path: Path,
) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(
        ["agent", "hook", "--client", "codex", "pre-tool", str(tmp_path)],
        stdout=stdout,
        stderr=stderr,
        stdin='{"tool_name":"Read"}',
    )

    assert exit_code == 2
    assert stdout.getvalue() == ""
    assert "asp-python agent hook moved to asp" in stderr.getvalue()
    assert "asp hook <event> --client codex" in stderr.getvalue()
