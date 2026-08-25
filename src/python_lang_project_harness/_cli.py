"""Command-line execution for the Python project harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from ._cli_args import CliOptions, ProtocolArgs, help_text
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
    protocol_args = ProtocolArgs.parse(args)
    if protocol_args is not None:
        return run_protocol_cli(
            protocol_args,
            stdout=selected_stdout,
            stderr=selected_stderr,
            stdin="" if stdin is None else stdin,
            cwd=selected_cwd,
        )
    try:
        options = CliOptions.parse(args)
        if options.help:
            selected_stdout.write(help_text())
            return 0
        project_root = options.project_root(cwd)
        if not project_root.exists():
            raise ValueError(f"project root does not exist: {project_root}")
        from ._render import render_python_lang_harness, render_python_lang_harness_json
        from ._runner import run_python_project_harness

        config = options.harness_config(project_root)
        report = run_python_project_harness(
            project_root,
            config=config,
            include_tests=options.include_tests,
            source_dir_names=options.source_dir_names,
            test_dir_names=options.test_dir_names,
            extra_path_names=options.extra_path_names,
        )
        if options.json:
            selected_stdout.write(render_python_lang_harness_json(report))
            selected_stdout.write("\n")
        elif options.agent_snapshot:
            from ._agent_snapshot import (
                render_python_project_harness_agent_snapshot_report,
            )
            from ._model import PythonHarnessConfig
            from ._project_config import read_python_project_harness_config

            selected_stdout.write(
                render_python_project_harness_agent_snapshot_report(
                    report,
                    config=(
                        config
                        or read_python_project_harness_config(project_root)
                        or PythonHarnessConfig()
                    ),
                )
            )
        else:
            selected_stdout.write(render_python_lang_harness(report))
        return 0 if report.is_clean else 1
    except ValueError as error:
        selected_stderr.write(f"{error}\n")
        return 2
