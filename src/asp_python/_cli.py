"""Command-line execution for the Python project harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from ._cli_args import ProtocolArgs, help_text
from ._cli_protocol import run_protocol_cli


def run_cli_from_env() -> int:
    """Run the CLI using process environment arguments."""

    from ._dev_command_log import start_dev_command_log

    args = sys.argv[1:]
    log = start_dev_command_log(args, Path.cwd())
    try:
        if args == ["serve"]:
            from ._runtime import serve_provider_runtime

            exit_code = serve_provider_runtime(Path.cwd())
            log.finish(exit_code)
            return exit_code
        stdin = "" if sys.stdin.isatty() else sys.stdin.read()
        exit_code = run_cli(args, stdin=stdin)
        log.finish(exit_code)
        return exit_code
    except Exception:
        log.finish(2)
        raise


def run_cli(
    args: list[str] | tuple[str, ...],
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    stdin: str | bytes | None = None,
    cwd: Path | None = None,
) -> int:
    """Run the default package-level Python harness CLI."""

    selected_stdout = sys.stdout if stdout is None else stdout
    selected_stderr = sys.stderr if stderr is None else stderr
    selected_cwd = Path.cwd() if cwd is None else cwd
    if not args or args[0] in {"--help", "-h"}:
        selected_stdout.write(help_text())
        return 0
    protocol_args = ProtocolArgs.parse(args)
    if protocol_args is not None:
        return run_protocol_cli(
            protocol_args,
            stdout=selected_stdout,
            stderr=selected_stderr,
            stdin="" if stdin is None else stdin,
            cwd=selected_cwd,
        )
    selected_stderr.write(f"unknown command: {args[0]}\n")
    return 2
