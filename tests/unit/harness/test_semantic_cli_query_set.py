"""Semantic CLI query-set protocol tests."""

from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

from semantic_search_fixture import write_search_fixture

from asp_python import run_cli


def test_cli_search_text_prefilter_large_project_records_runtime_cost(
    tmp_path: Path,
) -> None:
    if shutil.which("rg") is None:
        return
    write_search_fixture(tmp_path)
    generated = tmp_path / "src" / "pkg" / "generated"
    generated.mkdir()
    for index in range(140):
        (generated / f"candidate_{index}.py").write_text(
            f'def large_need_{index}() -> str:\n    return "LargeNeedle-{index}"\n',
            encoding="utf-8",
        )

    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "search",
            "lexical",
            "--query",
            "LargeNeedle",
            "--query",
            "large_need",
            "--query",
            "generated",
            "--owner",
            "src/pkg/service.py",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    packet = json.loads(stdout.getvalue())
    runtime_cost = packet["runtimeCost"]
    fields = runtime_cost["fields"]
    assert runtime_cost["sourceFilesParsed"] == fields["matchedFiles"]
    assert fields["candidateFiles"] > 128
    assert fields["minCandidateFiles"] == 128
    assert fields["mode"] == "text-query-prefilter"
    assert fields["queryTerms"] == 3
    assert fields["sourceSearchPasses"] == 1
    assert fields["fileListPasses"] == 1
    assert fields["candidateFileBasis"] == "all-python-files"
    assert fields["matchedFiles"] <= 17
    assert any(note["kind"] == "runtime-prefilter" for note in packet["notes"])


def test_cli_search_text_prefilter_skips_file_list_for_source_rich_terms(
    tmp_path: Path,
) -> None:
    if shutil.which("rg") is None:
        return
    write_search_fixture(tmp_path)
    generated = tmp_path / "src" / "pkg" / "generated"
    generated.mkdir()
    for index in range(140):
        (generated / f"source_rich_{index}.py").write_text(
            "\n".join(
                (
                    f"def LargeNeedle_{index}() -> str:",
                    f'    large_need = "generated-{index}"',
                    "    return large_need",
                    "",
                )
            ),
            encoding="utf-8",
        )

    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "search",
            "lexical",
            "--query",
            "LargeNeedle",
            "--query",
            "large_need",
            "--query",
            "generated",
            "--json",
            "--workspace",
            str(tmp_path),
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    packet = json.loads(stdout.getvalue())
    fields = packet["runtimeCost"]["fields"]
    assert fields["candidateFiles"] > 128
    assert fields["candidateFileBasis"] == "source-matched-files"
    assert fields["sourceSearchPasses"] == 1
    assert fields["fileListPasses"] == 0
    assert fields["prefilterTool"] == "rg"
    assert fields["matchedFiles"] <= 48
