from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import run_asp_python

if TYPE_CHECKING:
    from pathlib import Path


def test_modularity_rule_pack_blocks_large_class_only_service_module(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "services.py"
    source.write_text(_large_class_only_service_module_source(), encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-MOD-R006", str(source)),
    ]


def test_modularity_rule_pack_allows_large_single_signal_state_module(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "constants.py"
    source.write_text(_large_state_only_module_source(), encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [finding.rule_id for finding in report.findings] == []


def test_modularity_rule_pack_allows_large_single_return_literal_fixture(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "schema_fixture.py"
    source.write_text(_large_return_literal_fixture_module_source(), encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [finding.rule_id for finding in report.findings] == []


def test_modularity_rule_pack_blocks_large_module_with_long_function(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "orchestrator.py"
    source.write_text(_large_long_function_module_source(), encoding="utf-8")

    report = run_asp_python(tmp_path)

    findings = [
        finding for finding in report.findings if finding.rule_id == "PY-MOD-R006"
    ]
    assert len(findings) == 1
    assert findings[0].location.path == str(source)
    assert "1 long functions" in findings[0].summary
    assert "long function spans" in findings[0].requirement


def _large_class_only_service_module_source() -> str:
    parts = ['"""Large class-only service module for tests."""\n\n']
    for index in range(12):
        parts.append(
            f"class Service{index}:\n"
            "    def __init__(self, value: int) -> None:\n"
            "        self.value = value\n\n"
        )
        for method_index in range(6):
            parts.append(
                f"    def handle_{method_index}(self, input_value: int) -> int:\n"
            )
            for line in range(3):
                parts.append(f"        value_{line} = input_value + {line}\n")
            parts.append("        return value_0 + self.value\n\n")
    return "".join(parts)


def _large_state_only_module_source() -> str:
    parts = ['"""Large generated constants module for tests."""\n\n']
    parts.append("VALUES = [\n")
    for index in range(240):
        parts.append(f"    {index},\n")
    parts.append("]\n")
    return "".join(parts)


def _large_return_literal_fixture_module_source() -> str:
    parts = ['"""Large schema fixture module for tests."""\n\n']
    parts.append("def fixture() -> dict[str, object]:\n")
    parts.append("    return {\n")
    for index in range(230):
        parts.append(f'        "field_{index}": {index},\n')
    parts.append("    }\n")
    return "".join(parts)


def _large_long_function_module_source() -> str:
    parts = ['"""Large orchestrator module for tests."""\n\n']
    parts.append("def run(value: int) -> int:\n")
    parts.append("    total = value\n")
    for index in range(230):
        parts.append(f"    total += {index}\n")
    parts.append("    return total\n")
    return "".join(parts)
