from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from syrupy.extensions.json import JSONSnapshotExtension

from asp_python import (
    run_python_lang_harness,
)

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from asp_python import AspPythonReport


_SCENARIO = (
    Path(__file__).parent / "scenarios" / "software_criteria" / "control_flow_v1"
)


class _ScenarioJsonSnapshotExtension(JSONSnapshotExtension):
    @classmethod
    def dirname(cls, *, test_location: Any) -> str:
        return str(_SCENARIO / "expect")

    @classmethod
    def get_file_basename(cls, *, test_location: Any, index: object) -> str:
        if isinstance(index, str):
            return index
        return super().get_file_basename(test_location=test_location, index=index)


def test_py_software_criterion_control_flow_v1_snapshot(
    tmp_path: Path,
    snapshot: SnapshotAssertion,
) -> None:
    _copy_inputs(_SCENARIO / "inputs", tmp_path)

    report = run_python_lang_harness([tmp_path / "criterion.py"])
    filtered = _filter_software_criterion_findings(report)
    findings = [
        {
            "rule_id": finding.rule_id,
            "summary": finding.summary,
            "line": finding.location.line,
            "label": finding.label,
            "softwareCriteria": finding.labels.get("softwareCriteria"),
        }
        for finding in filtered.findings
    ]

    assert {finding["softwareCriteria"] for finding in findings} == {
        "control-flow.decision-stack",
        "control-flow.traversal-knot",
        "control-flow.literal-dispatch-chain",
        "control-flow.broad-linear-phase",
        "native-idiom.manual-transform-loop",
    }
    assert (
        snapshot(name="findings", extension_class=_ScenarioJsonSnapshotExtension)
        == findings
    )


def test_py_software_criterion_control_flow_v1_scenario_benchmark_contract() -> None:
    scenario = tomllib.loads((_SCENARIO / "scenario.toml").read_text(encoding="utf-8"))
    benchmark = tomllib.loads(
        (_SCENARIO / "benchmark.toml").read_text(encoding="utf-8")
    )
    findings = json.loads(
        (_SCENARIO / "expect" / "findings.json").read_text(encoding="utf-8")
    )

    assert scenario["policy_ids"] == [
        "PYTHON-AGENT-CONTROL-FLOW-001",
        "PYTHON-AGENT-NATIVE-IDIOM-001",
    ]
    assert scenario["inputs"] == "inputs"
    assert scenario["expected"] == "expect"
    assert _fixture_files(_SCENARIO / scenario["inputs"])
    assert _fixture_files(_SCENARIO / scenario["expected"])

    trigger = scenario["policy_trigger"]
    expected_rule_ids = trigger["expected_rule_ids"]
    expected_criteria = trigger["expected_criteria"]
    assert trigger["kind"] == "software-criterion"
    assert trigger["evidence"] == "expect/findings.json"
    assert "inputs/criterion.py" in trigger["trigger"]
    assert "AI agent" in trigger["agent_failure_mode"]
    assert "Split" in trigger["expected_resolution"]
    assert expected_rule_ids == [
        "PY-AGENT-POLICY-009",
        "PY-AGENT-POLICY-010",
        "PY-AGENT-POLICY-011",
    ]
    assert {finding["rule_id"] for finding in findings} == set(expected_rule_ids)
    assert {finding["softwareCriteria"] for finding in findings} == set(
        expected_criteria
    )

    assert benchmark["harness"] == "pytest"
    assert (
        benchmark["test"] == "tests/unit/harness/test_software_criterion_snapshots.py"
    )
    _assert_benchmark_durations(benchmark)
    comparison = benchmark["input_expected_comparison"]
    assert comparison["input_total"] == "19ms"
    assert comparison["expected_total"] == "8ms"
    assert comparison["input_memory_bytes"] == 8388608
    assert comparison["expected_memory_bytes"] == 6291456
    assert "low-quality input patterns" in comparison["interpretation"]


def _copy_inputs(source_dir: Path, destination_dir: Path) -> None:
    for source in source_dir.rglob("*"):
        if source.is_dir():
            continue
        destination = destination_dir / source.relative_to(source_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _filter_software_criterion_findings(
    report: AspPythonReport,
) -> AspPythonReport:
    return replace(
        report,
        findings=tuple(
            finding
            for finding in report.findings
            if finding.rule_id
            in {"PY-AGENT-POLICY-009", "PY-AGENT-POLICY-010", "PY-AGENT-POLICY-011"}
        ),
    )


def _fixture_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file()]


def _assert_benchmark_durations(benchmark: dict[str, Any]) -> None:
    for field in [
        "target_total",
        "max_total",
        "observed_total",
        "regression_budget",
    ]:
        value = benchmark[field]
        assert isinstance(value, str)
        suffix = next(
            suffix for suffix in ("ns", "us", "ms", "s") if value.endswith(suffix)
        )
        assert value.removesuffix(suffix).isdigit()
    assert benchmark["memory_budget_bytes"] > 0
    assert benchmark["observed_memory_bytes"] > 0
