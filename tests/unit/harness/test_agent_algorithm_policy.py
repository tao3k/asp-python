from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from snapshot_support import assert_snapshot, normalize_temp_root

from asp_python import (
    render_python_lang_harness,
    run_python_lang_harness,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_py_agent_r009_algorithm_shape_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '''
"""Service algorithms."""


def classify(kind: str, rows: list[object]) -> int:
    for row in rows:
        if row:
            if kind == "alpha":
                return 1
            elif kind == "beta":
                return 2
            elif kind == "gamma":
                return 3
            elif kind == "delta":
                return 4
            else:
                return 0
    return -1
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])
    filtered = replace(
        report,
        findings=tuple(
            finding
            for finding in report.findings
            if finding.rule_id == "PY-AGENT-POLICY-009"
        ),
    )
    rendered = normalize_temp_root(render_python_lang_harness(filtered), tmp_path)

    assert filtered.findings, "expected PY-AGENT-POLICY-009 finding"
    assert (
        "control-flow.literal-dispatch-chain"
        in filtered.findings[0].labels["softwareCriteria"]
    )
    assert_snapshot(
        "unit_test__agent_policy_snapshot__py_agent_r009_algorithm_shape",
        rendered,
        source="tests/unit/harness/test_agent_algorithm_policy.py",
    )


def test_py_agent_r009_decision_stack_signal_label(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '''
"""Service algorithms."""


def classify(enabled: bool, ready: bool, valid: bool, active: bool) -> int:
    if enabled:
        if ready:
            if valid:
                if active:
                    return 1
    return 0
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])

    findings = tuple(
        finding
        for finding in report.findings
        if finding.rule_id == "PY-AGENT-POLICY-009"
    )
    assert len(findings) == 1
    assert findings[0].labels["softwareCriteria"] == "control-flow.decision-stack"


def test_py_agent_r009_traversal_knot_signal_label(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '''
"""Service algorithms."""


def classify(groups: list[list[int]]) -> int:
    total = 0
    for group in groups:
        for value in group:
            if value > 10:
                total += value
            elif value < 0:
                total -= value
            elif value == 0:
                total += 0
            else:
                total += 1
    return total
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])

    findings = tuple(
        finding
        for finding in report.findings
        if finding.rule_id == "PY-AGENT-POLICY-009"
    )
    assert len(findings) == 1
    assert findings[0].labels["softwareCriteria"] == "control-flow.traversal-knot"


def test_py_agent_r009_accepts_explicit_match_dispatch(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '''
"""Service algorithms."""


def classify(kind: str) -> int:
    match kind:
        case "alpha":
            return 1
        case "beta":
            return 2
        case "gamma":
            return 3
        case "delta":
            return 4
        case _:
            return 0
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])

    assert not any(
        finding.rule_id == "PY-AGENT-POLICY-009" for finding in report.findings
    )


def test_py_agent_r010_function_compactness_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(_broad_linear_function_source(), encoding="utf-8")

    report = run_python_lang_harness([source])
    filtered = replace(
        report,
        findings=tuple(
            finding
            for finding in report.findings
            if finding.rule_id == "PY-AGENT-POLICY-010"
        ),
    )
    rendered = normalize_temp_root(render_python_lang_harness(filtered), tmp_path)

    assert filtered.findings, "expected PY-AGENT-POLICY-010 finding"
    assert (
        filtered.findings[0].labels["softwareCriteria"]
        == "control-flow.broad-linear-phase"
    )
    assert_snapshot(
        "unit_test__agent_policy_snapshot__py_agent_r010_function_compactness",
        rendered,
        source="tests/unit/harness/test_agent_algorithm_policy.py",
    )


def test_py_agent_r011_native_idiom_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "service.py"
    source.write_text(
        '''
"""Service algorithms."""


def has_admin(values: list[str]) -> bool:
    total = 0
    for value in values:
        total += len(value)
    counts = {}
    groups = {}
    for value in values:
        if value not in counts:
            counts[value] = 0
        counts[value] += 1
    for value in values:
        if value not in groups:
            groups[value] = []
        groups[value].append(value)
    names = []
    for value in values:
        if value:
            names.append(value.strip())
    for name in names:
        if name == "admin":
            return True
    return False
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])
    filtered = replace(
        report,
        findings=tuple(
            finding
            for finding in report.findings
            if finding.rule_id == "PY-AGENT-POLICY-011"
        ),
    )
    rendered = normalize_temp_root(render_python_lang_harness(filtered), tmp_path)

    assert filtered.findings, "expected PY-AGENT-POLICY-011 finding"
    assert (
        filtered.findings[0].labels["softwareCriteria"]
        == "native-idiom.manual-transform-loop"
    )
    assert_snapshot(
        "unit_test__agent_policy_snapshot__py_agent_r011_native_idiom",
        rendered,
        source="tests/unit/harness/test_agent_algorithm_policy.py",
    )


def test_py_agent_r012_type_shape_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "models.py"
    source.write_text(
        '''
"""Model shapes."""


class CustomerRecord:
    def __init__(self, name: str, email: str, active: bool) -> None:
        self.name = name
        self.email = email
        self.active = active

    def __repr__(self) -> str:
        return self.name
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])
    filtered = replace(
        report,
        findings=tuple(
            finding
            for finding in report.findings
            if finding.rule_id == "PY-AGENT-POLICY-012"
        ),
    )
    rendered = normalize_temp_root(render_python_lang_harness(filtered), tmp_path)

    assert filtered.findings, "expected PY-AGENT-POLICY-012 finding"
    assert_snapshot(
        "unit_test__agent_policy_snapshot__py_agent_r012_type_shape",
        rendered,
        source="tests/unit/harness/test_agent_algorithm_policy.py",
    )


def test_py_agent_r012_accepts_dataclass_anchor(tmp_path: Path) -> None:
    source = tmp_path / "models.py"
    source.write_text(
        '''
"""Model shapes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerRecord:
    name: str
    email: str
    active: bool
''',
        encoding="utf-8",
    )

    report = run_python_lang_harness([source])

    assert not any(
        finding.rule_id == "PY-AGENT-POLICY-012" for finding in report.findings
    )


def _broad_linear_function_source() -> str:
    lines = [
        '"""Service algorithms."""',
        "",
        "",
        "def summarize(value: int) -> int:",
    ]
    for index in range(15):
        lines.append(f"    step_{index} = value + {index}")
    lines.append("    return step_0")
    return "\n".join(lines) + "\n"
