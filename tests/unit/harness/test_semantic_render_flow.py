"""Semantic search flow renderer contract tests."""

from __future__ import annotations

from asp_python._semantic_search_render_flow import finding_lines


def test_semantic_search_findings_render_path_first() -> None:
    lines = finding_lines(
        {
            "findings": [
                {
                    "ruleId": "PY-AGENT-POLICY-001",
                    "count": 1,
                    "location": {
                        "path": "src/pkg/service.py",
                        "line": 3,
                        "column": 1,
                    },
                    "severity": "info",
                }
            ]
        }
    )

    assert lines == [
        "|find PY-AGENT-POLICY-001 x1 path=src/pkg/service.py line=3 column=1 node=O:src/pkg/service.py severity=info"
    ]
    assert "at=O:" not in lines[0]
