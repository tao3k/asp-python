from __future__ import annotations

from asp_python import (
    PythonProjectPolicyRulePack,
    python_project_policy_rules,
)


def test_project_policy_rule_pack_descriptor_and_catalog_are_stable() -> None:
    descriptor = PythonProjectPolicyRulePack().descriptor()
    rules = python_project_policy_rules()

    assert descriptor.id == "python.project_policy"
    assert descriptor.to_dict()["domains"] == [
        "project-policy",
        "packaging",
        "python",
    ]
    assert [rule.rule_id for rule in rules] == [
        "PY-AGENT-PROJECT-001",
        "PY-AGENT-PROJECT-002",
        "PY-AGENT-PROJECT-003",
        "PY-AGENT-PROJECT-004",
        "PY-AGENT-PROJECT-005",
        "PY-AGENT-PROJECT-006",
        "PY-AGENT-PROJECT-007",
        "PY-AGENT-PROJECT-008",
        "PY-AGENT-PROJECT-009",
        "PY-AGENT-PROJECT-010",
        "PY-AGENT-PROJECT-011",
    ]
