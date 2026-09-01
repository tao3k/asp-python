"""Semantic CLI lexical protocol tests."""

from __future__ import annotations

import io
from pathlib import Path

from semantic_search_fixture import require_compact_graph_renderer, write_search_fixture

from asp_python._cli import run_cli


def test_cli_search_lexical_query_set(tmp_path: Path) -> None:
    write_search_fixture(tmp_path)
    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "search",
            "lexical",
            "--query",
            "build",
            "--query",
            "Session",
            "owner",
            "tests",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )
    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith('[search-lexical] q="build,Session" querySet=2')
    assert "selector=lexical-set" in rendered
    for line in rendered.splitlines():
        if line.startswith("|seed "):
            assert ",owner:" not in line
            assert ",tests:" not in line


def test_cli_search_lexical_matches_path_only_candidate(tmp_path: Path) -> None:
    require_compact_graph_renderer()
    write_search_fixture(tmp_path)
    path_owner = tmp_path / "src" / "pkg" / "hook_runtime.py"
    path_owner.write_text(
        '"""Path-only lexical owner."""\n\ndef execute() -> None:\n    pass\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "search",
            "lexical",
            "--query",
            "hookruntime",
            "--query",
            "execute",
            "owner",
            "tests",
            "--view",
            "seeds",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )
    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-lexical] q=hookruntime,execute")
    assert "O=owner:path(src/pkg/hook_runtime.py)!owner" in rendered
    assert "rank=Q,O,T frontier=Q.lexical,O.owner,T.tests" in rendered
    assert "|seed " not in rendered


def test_protocol_search_lexical_query_uses_fast_frontier(
    tmp_path: Path,
) -> None:
    from asp_python._cli_args import ProtocolArgs
    from asp_python._cli_protocol import run_protocol_cli

    write_search_fixture(tmp_path)
    path_owner = tmp_path / "src" / "pkg" / "hook_runtime.py"
    path_owner.write_text(
        '"""Path-only lexical owner."""\n\ndef execute() -> None:\n    pass\n',
        encoding="utf-8",
    )
    args = ProtocolArgs.parse(
        [
            "search",
            "lexical",
            "--query",
            "hookruntime",
            "--query",
            "execute",
            "owner",
            "tests",
            "--view",
            "seeds",
            "--workspace",
            str(tmp_path),
        ]
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    assert args is not None
    exit_code = run_protocol_cli(
        args,
        stdout=stdout,
        stderr=stderr,
        stdin="",
        cwd=tmp_path,
    )
    rendered = stdout.getvalue()
    assert stderr.getvalue() == ""
    assert exit_code == 0
    assert rendered.startswith(
        "[search-lexical] q=hookruntime,execute querySet=2 selector=lexical-set "
        "view=hits alg=query-set-owner-resolution"
    )
    assert "Q=query:term(hookruntime,execute)!lexical" in rendered
    assert "entries=owner-query(O,Q=>items+tests+dependency-usage)" in rendered
    assert "rank=Q,O,T frontier=Q.lexical,O.owner,T.tests" in rendered
    assert "|seed " not in rendered


def test_protocol_search_lexical_query_uses_native_prefilter_without_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from asp_python import (
        _semantic_search_prefilter,
        _semantic_search_prefilter_file_scan,
    )
    from asp_python._cli_args import ProtocolArgs
    from asp_python._cli_protocol import run_protocol_cli

    monkeypatch.setattr(_semantic_search_prefilter.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        _semantic_search_prefilter_file_scan.shutil,
        "which",
        lambda _name: None,
    )
    write_search_fixture(tmp_path)
    path_owner = tmp_path / "src" / "pkg" / "hook_runtime.py"
    path_owner.write_text(
        '"""Path-only lexical owner."""\n\ndef execute() -> None:\n    pass\n',
        encoding="utf-8",
    )
    args = ProtocolArgs.parse(
        [
            "search",
            "lexical",
            "--query",
            "hookruntime",
            "--query",
            "execute",
            "owner",
            "tests",
            "--view",
            "seeds",
            "--workspace",
            str(tmp_path),
        ]
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    assert args is not None
    exit_code = run_protocol_cli(
        args,
        stdout=stdout,
        stderr=stderr,
        stdin="",
        cwd=tmp_path,
    )
    rendered = stdout.getvalue()
    assert stderr.getvalue() == ""
    assert exit_code == 0
    assert rendered.startswith(
        "[search-lexical] q=hookruntime,execute querySet=2 selector=lexical-set "
        "view=hits alg=query-set-owner-resolution"
    )
    assert "Q=query:term(hookruntime,execute)!lexical" in rendered
    assert "O=owner:path(src/pkg/hook_runtime.py)!owner" in rendered
    assert "entries=owner-query(O,Q=>items+tests+dependency-usage)" in rendered


def test_protocol_search_lexical_source_query_uses_rglob_source_without_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from asp_python import (
        _semantic_search_prefilter,
        _semantic_search_prefilter_file_scan,
    )
    from asp_python._cli_args import ProtocolArgs
    from asp_python._cli_protocol import run_protocol_cli

    monkeypatch.setattr(_semantic_search_prefilter.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        _semantic_search_prefilter_file_scan.shutil,
        "which",
        lambda _name: None,
    )
    write_search_fixture(tmp_path)
    for index in range(130):
        filler = tmp_path / "src" / "pkg" / f"filler_{index:03d}.py"
        filler.write_text(f"VALUE_{index} = {index}\n", encoding="utf-8")
    query_owner = tmp_path / "src" / "pkg" / "cli_query.py"
    query_owner.write_text(
        "def run_query_command() -> None:\n    pass\n",
        encoding="utf-8",
    )
    protocol_owner = tmp_path / "src" / "pkg" / "cli_protocol.py"
    protocol_owner.write_text(
        "from .cli_query import run_query_command\n",
        encoding="utf-8",
    )
    args = ProtocolArgs.parse(
        [
            "search",
            "lexical",
            "--query",
            "run_query_command",
            "--query",
            "command",
            "owner",
            "tests",
            "--view",
            "seeds",
            "--workspace",
            str(tmp_path),
        ]
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    assert args is not None
    exit_code = run_protocol_cli(
        args,
        stdout=stdout,
        stderr=stderr,
        stdin="",
        cwd=tmp_path,
    )
    rendered = stdout.getvalue()
    assert stderr.getvalue() == ""
    assert exit_code == 0
    assert rendered.startswith(
        "[search-lexical] q=run_query_command,command querySet=2"
    )
    assert "Q=query:term(run_query_command,command)!lexical" in rendered
    assert "O=owner:path(src/pkg/cli_query.py)!owner" in rendered
    assert "entries=owner-query(O,Q=>items+tests+dependency-usage)" in rendered
    assert "rglob-source" in rendered
