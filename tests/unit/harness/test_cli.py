from __future__ import annotations

import io
from typing import TYPE_CHECKING

from asp_python import run_cli

if TYPE_CHECKING:
    from pathlib import Path


def test_cli_help_advertises_the_current_provider_protocol() -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["--help"], stdout=stdout)

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert "asp-python search <view>" in rendered
    assert "asp python query --selector" in rendered
    assert "asp-python evidence graph" in rendered
    assert "asp-python agent doctor" in rendered


def test_cli_subcommand_help_advertises_exact_projection() -> None:
    for args in (["search", "--help"], ["query", "--help"]):
        stdout = io.StringIO()

        exit_code = run_cli(args, stdout=stdout)

        rendered = stdout.getvalue()
        assert exit_code == 0
        assert "--selector <exact-structural-selector>" in rendered
        assert "--projection <source|callable-skeleton>" in rendered


def test_cli_agent_guide_advertises_exact_source_route(tmp_path: Path) -> None:
    stdout = io.StringIO()

    exit_code = run_cli(["agent", "guide", str(tmp_path)], stdout=stdout)

    assert exit_code == 0
    assert (
        "asp python query --selector <exact-structural-selector>" in stdout.getvalue()
    )
    assert "|policy authority=asp-python-api trigger=pytest-plugin" in stdout.getvalue()


def test_cli_without_command_renders_help_instead_of_running_policy() -> None:
    stdout = io.StringIO()

    exit_code = run_cli((), stdout=stdout)

    assert exit_code == 0
    assert stdout.getvalue().startswith("asp-python ")
