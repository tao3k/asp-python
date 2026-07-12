"""Fast semantic CLI prime frontier tests."""

from __future__ import annotations

import io
import time
from pathlib import Path

import pytest

from python_lang_project_harness import run_cli

FAST_SEARCH_BUDGET_SECONDS = 0.25


def test_cli_search_prime_seed_view_uses_fast_frontier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "src" / "pkg" / "service.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("def build():\n    return 1\n", encoding="utf-8")

    from python_lang_project_harness import _cli_protocol

    def fail_full_harness(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("full harness should not run for prime seed view")

    monkeypatch.setattr(_cli_protocol, "_run_search_harness", fail_full_harness)
    stdout = io.StringIO()

    started_at = time.perf_counter()
    exit_code = run_cli(
        ["search", "prime", "--view", "seeds", "--workspace", str(tmp_path)],
        stdout=stdout,
    )
    elapsed = time.perf_counter() - started_at

    rendered = stdout.getvalue()
    assert exit_code == 0
    assert rendered.startswith("[search-prime]")
    assert "alg=fast-prime-frontier-v1" in rendered
    assert "|decision purpose=decision-primer" in rendered
    assert "answer=false code=false" in rendered
    assert (
        "capabilities=pipe,lexical,fd-query,rg-query,owner-items,selector-code,treesitter-query"
        in rendered
    )
    assert "ladder=pipe>lexical>fd-query|rg-query>owner-items>selector-code" in rendered
    assert (
        "history=asp-artifacts:directReadRisk,repeatedPrime,repeatedPipe,bestPath"
        in rendered
    )
    assert "risk=broad-direct-read,manual-window-scan,repeat-prime" in rendered
    assert (
        "next=\"asp python search pipe '<question-or-feature-term>' --workspace <workspace-root> --view seeds\""
        in rendered
    )
    assert "owner:path(src/pkg/service.py)" in rendered
    assert "frontier=O1.owner" in rendered
    assert (
        "legend: ID=kind:role(value)!next; entries profile(selectors=>returns); frontier ID.next"
        in rendered
    )
    assert (
        "entries=owner-tests(O=>covering-tests+test-entrypoints+fixtures)" in rendered
    )
    assert "A1=owner-items" not in rendered
    assert "recommendedNext=owner-items" not in rendered
    assert elapsed < FAST_SEARCH_BUDGET_SECONDS
