"""Protocol command dispatch for the Python harness CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from ._cli_agent import (
    render_agent_doctor,
    render_agent_doctor_json,
    render_agent_guide,
)
from ._cli_args import ProtocolArgs, help_text
from ._cli_search_runtime import _render_search_code_only, _run_search_harness


def run_protocol_cli(
    args: ProtocolArgs,
    *,
    stdout: TextIO,
    stderr: TextIO,
    stdin: str,
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
    if args.command == "evidence":
        return _run_evidence_command(args, project_root=project_root, stdout=stdout)
    if args.command == "ast-patch":
        return _run_ast_patch_command(
            args, project_root=project_root, stdout=stdout, stdin=stdin
        )

    try:
        fast_exit = _run_fast_protocol_command(
            args,
            project_root=project_root,
            stdout=stdout,
            stdin=stdin,
        )
        if fast_exit is not None:
            return fast_exit
        return _run_harness_protocol_command(
            args,
            project_root=project_root,
            stdout=stdout,
            stdin=stdin,
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


def _run_evidence_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
) -> int:
    from ._evidence_graph import (
        build_python_evidence_graph,
        render_python_evidence_graph,
        render_python_evidence_graph_json,
    )
    from ._evidence_graph_turbo import (
        build_python_evidence_analysis_request,
        render_python_evidence_analysis_request,
        render_python_evidence_analysis_request_json,
    )

    if args.action == "graph":
        graph = build_python_evidence_graph(project_root)
        stdout.write(
            render_python_evidence_graph_json(graph)
            if args.json
            else render_python_evidence_graph(graph)
        )
        return 0
    if args.action == "analyze":
        request = build_python_evidence_analysis_request(project_root)
        stdout.write(
            render_python_evidence_analysis_request_json(request)
            if args.json
            else render_python_evidence_analysis_request(request)
        )
        return 0
    raise ValueError("expected evidence <graph|analyze>")


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


def _run_fast_protocol_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
    stdin: str,
) -> int | None:
    rendered = _render_fast_protocol_command(
        args,
        project_root=project_root,
        stdin=stdin,
    )
    if rendered is None:
        return None
    stdout.write(rendered)
    return 0


def _render_fast_protocol_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdin: str,
) -> str | None:
    from ._semantic_graph_facts import render_semantic_graph_facts
    from ._semantic_search_ingest_fast import render_fast_empty_ingest_search
    from ._semantic_search_lexical_fast import render_fast_lexical_seed_search
    from ._semantic_search_owner_fast import render_fast_owner_seed_search
    from ._semantic_search_prime_fast import render_fast_prime_search
    from ._workspace_scope import render_workspace_scope

    renderers = (
        lambda: render_workspace_scope(args, project_root=project_root),
        lambda: render_semantic_graph_facts(
            args, project_root=project_root, stdin=stdin
        ),
        lambda: render_fast_empty_ingest_search(args, project_root, stdin),
        lambda: render_fast_prime_search(args, project_root),
        lambda: render_fast_owner_seed_search(args, project_root),
        lambda: render_fast_lexical_seed_search(args, project_root),
    )
    for render in renderers:
        rendered = render()
        if rendered is not None:
            return rendered
    return None


def _run_harness_protocol_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
    stdin: str,
) -> int:
    report, runtime_cost = _run_search_harness(project_root, args)
    if args.command == "query":
        return _run_query_command(
            args, report=report, project_root=project_root, stdout=stdout
        )
    if args.command == "check":
        return _run_check_command(args, report=report, stdout=stdout)
    return _run_search_command(
        args,
        report=report,
        runtime_cost=runtime_cost,
        stdout=stdout,
        stdin=stdin,
    )


def _run_query_command(
    args: ProtocolArgs,
    *,
    report: object,
    project_root: Path,
    stdout: TextIO,
) -> int:
    from ._cli_query import run_query_command

    return run_query_command(
        args,
        report=report,
        project_root=project_root,
        stdout=stdout,
    )


def _run_check_command(
    args: ProtocolArgs,
    *,
    report: object,
    stdout: TextIO,
) -> int:
    from ._render import (
        render_python_lang_harness,
        render_python_lang_harness_json,
    )

    if args.json:
        stdout.write(render_python_lang_harness_json(report))
        stdout.write("\n")
    else:
        stdout.write(render_python_lang_harness(report))
    return 0 if report.is_clean else 1


def _run_search_command(
    args: ProtocolArgs,
    *,
    report: object,
    runtime_cost: dict[str, object] | None,
    stdout: TextIO,
    stdin: str,
) -> int:
    from ._semantic_search import (
        PythonSemanticSearchOptions,
        build_python_semantic_search_packet,
        render_python_semantic_search_packet,
        render_python_semantic_search_packet_json,
    )

    packet = build_python_semantic_search_packet(
        report,
        PythonSemanticSearchOptions(
            view=args.view or "prime",
            query=args.query,
            item_query=args.item_query,
            query_set=args.query_set,
            owner_path=args.owner_path,
            dependency=args.dependency,
            pipes=args.pipes,
            render_mode=args.render_mode,
            stdin=stdin,
            runtime_cost=runtime_cost,
        ),
    )
    if args.code_only:
        stdout.write(_render_search_code_only(packet))
    else:
        stdout.write(
            render_python_semantic_search_packet_json(packet)
            if args.json
            else render_python_semantic_search_packet(packet)
        )
    return 0
