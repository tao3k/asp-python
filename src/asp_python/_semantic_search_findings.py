"""Finding facts for Python semantic-search packets."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import (
    location_from_source,
    semantic_search_display_path,
)
from ._semantic_search_model import MAX_FINDINGS

if TYPE_CHECKING:
    from ._model import AspPythonFinding, AspPythonReport


def finding_facts(
    report: AspPythonReport,
    project_root: Path,
    *,
    owner_paths: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return grouped harness findings."""

    counter: Counter[tuple[str, str, str, str]] = Counter()
    finding_by_key: dict[tuple[str, str, str, str], AspPythonFinding] = {}
    for finding in report.findings:
        path = semantic_search_display_path(finding.location.path or ".", project_root)
        if owner_paths is not None and path not in owner_paths:
            continue
        key = (finding.rule_id, finding.severity.value, finding.title, path)
        counter[key] += 1
        finding_by_key[key] = finding
    return [
        {
            "ruleId": finding_by_key[key].rule_id,
            "severity": finding_by_key[key].severity.value,
            "count": count,
            "title": finding_by_key[key].title,
            "location": location_from_source(
                finding_by_key[key].location, project_root
            ),
        }
        for key, count in counter.most_common(MAX_FINDINGS)
    ]
