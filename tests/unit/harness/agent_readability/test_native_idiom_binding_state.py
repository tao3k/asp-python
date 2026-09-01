from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import run_python_lang_harness

if TYPE_CHECKING:
    from pathlib import Path


def test_py_agent_r011_ignores_reassigned_empty_accumulators(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '''
"""Service algorithms."""


def collect(values: list[int]) -> tuple[list[int], dict[int, int], int]:
    items = []
    items = preload_items()
    for value in values:
        items.append(value)
    counts = {}
    counts = preload_counts()
    for value in values:
        if value not in counts:
            counts[value] = 0
        counts[value] += 1
    total = 0
    total = preload_total()
    for value in values:
        total += value
    return items, counts, total
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])

    assert not any(
        finding.rule_id == "PY-AGENT-POLICY-011" for finding in report.findings
    )
