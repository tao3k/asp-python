from __future__ import annotations

import os
import tempfile
from pathlib import Path

from asp_python._agent_policy_catalog import python_agent_policy_rules
from asp_python._harness_rules import (
    python_harness_rules_markdown,
    render_python_harness_rules_markdown,
    write_python_harness_rules_to_unit_tests,
)
from asp_python._modern_design_catalog import (
    python_modern_design_rules,
)
from asp_python._modularity import python_modularity_rules
from asp_python._project_policy_catalog import (
    python_project_policy_rules,
)
from asp_python._test_layout_catalog import python_test_layout_rules


def _harness_rules_rule_ids() -> list[str]:
    rule_ids: list[str] = []
    for line in python_harness_rules_markdown().splitlines():
        rule_id, _ = line.removeprefix("- ").split(": ", 1)
        rule_ids.append(rule_id)
    return rule_ids


def _catalog_rule_ids() -> list[str]:
    rules = (
        *python_agent_policy_rules(),
        *python_modern_design_rules(),
        *python_modularity_rules(),
        *python_project_policy_rules(),
        *python_test_layout_rules(),
    )
    return [rule.rule_id for rule in rules]


def test_harness_rules_markdown_is_plain_rule_id_list() -> None:
    count = 0
    for index, line in enumerate(python_harness_rules_markdown().splitlines(), start=1):
        assert line.startswith("- "), index
        rule_id, sentence = line.removeprefix("- ").split(": ", 1)

        assert rule_id.startswith(
            (
                "PY-AGENT-R",
                "PY-AGENT-POLICY",
                "PY-AGENT-PROJECT",
                "PY-MOD-R",
                "PY-PROJ-R",
                "PY-TEST-R",
            )
        )
        assert sentence.endswith(".")
        assert sum(sentence.count(mark) for mark in ".!?") == 1
        count += 1

    assert count == 32


def test_harness_rules_ids_match_rule_catalog() -> None:
    assert sorted(_harness_rules_rule_ids()) == sorted(_catalog_rule_ids())


def test_generated_harness_rules_matches_unit_fixture() -> None:
    unit_dir = Path(__file__).resolve().parent
    fixture = unit_dir / "harness-rules.generated.md"
    if os.environ.get("UPDATE_HARNESS_RULES"):
        write_python_harness_rules_to_unit_tests(unit_dir)

    assert fixture.read_text(encoding="utf-8") == render_python_harness_rules_markdown()


def test_harness_rules_writer_targets_requested_unit_dir() -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = write_python_harness_rules_to_unit_tests(Path(directory))

        assert output == Path(directory) / "harness-rules.generated.md"
        assert (
            output.read_text(encoding="utf-8") == render_python_harness_rules_markdown()
        )
