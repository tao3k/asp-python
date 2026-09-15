"""Protocol command dispatch for the ASP Python CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from ._cli_agent import (
    render_agent_doctor,
    render_agent_doctor_json,
    render_agent_guide,
)
from ._cli_args import ProtocolArgs, help_text


def run_protocol_cli(
    args: ProtocolArgs,
    *,
    stdout: TextIO,
    stderr: TextIO,
    stdin: str | bytes,
    cwd: Path,
) -> int:
    if args.command == "error":
        stderr.write(f"{args.error}\n")
        return 2
    if args.command == "help":
        stdout.write(help_text())
        return 0
    project_root = _resolve_project_root(args, cwd)
    if args.command == "agent":
        return _run_agent_command(args, project_root=project_root, stdout=stdout)
    if args.command == "ast-patch":
        return _run_ast_patch_command(
            args, project_root=project_root, stdout=stdout, stdin=stdin
        )

    try:
        if args.command != "query":
            raise ValueError("unsupported provider command")
        return _run_query_protocol_command(
            args, project_root=project_root, stdout=stdout
        )
    except ValueError as error:
        stderr.write(f"{error}\n")
        return 3


def _resolve_project_root(args: ProtocolArgs, cwd: Path) -> Path:
    project_root = (cwd / args.project_root).resolve() if args.project_root else cwd
    if args.package_path is not None:
        return (project_root / args.package_path).resolve()
    return project_root


def _run_agent_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
) -> int:
    if args.action == "guide":
        stdout.write(render_agent_guide(project_root))
        return 0
    if args.json:
        stdout.write(render_agent_doctor_json(project_root))
    else:
        stdout.write(render_agent_doctor(project_root))
    return 0


def _run_ast_patch_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
    stdin: str,
) -> int:
    from ._cli_ast_patch import run_ast_patch_command

    return run_ast_patch_command(
        args, project_root=project_root, stdout=stdout, stdin=stdin
    )


def _run_query_protocol_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
) -> int:
    from ._cli_query import run_query_command
    from ._rule_packs import resolve_asp_python_project_config
    from ._runner import run_asp_python

    report = run_asp_python(
        project_root,
        config=resolve_asp_python_project_config(project_root, None, rule_packs=None),
    )
    return run_query_command(
        args,
        report=report,
        project_root=project_root,
        stdout=stdout,
    )
