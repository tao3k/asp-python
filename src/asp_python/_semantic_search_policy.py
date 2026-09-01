"""Own semantic search policy findings for Python agent search and repair."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._agent_policy_catalog import python_agent_policy_rules
from ._model import AspPythonReport, AspPythonRule
from ._project_policy_catalog import python_project_policy_rules
from ._semantic_search_common import compact_fields, header, path_hit

PROJECT_POLICY_CATALOG_OWNER = "src/asp_python/_project_policy_catalog.py"
AGENT_POLICY_CATALOG_OWNER = "src/asp_python/_agent_policy_catalog.py"

PROJECT_POLICY_TEST_PATHS = (
    "tests/unit/harness/project_policy/test_catalog.py",
    "tests/unit/harness/project_policy/test_layout.py",
    "tests/unit/harness/test_policy_contract.py",
    "tests/unit/harness/test_policy_snapshots.py",
)
AGENT_POLICY_TEST_PATHS = (
    "tests/unit/harness/test_agent_policy.py",
    "tests/unit/harness/test_agent_policy_snapshots.py",
    "tests/unit/harness/test_policy_contract.py",
)


def policy_payload(
    report: AspPythonReport,
    facts: Any,
    project_root: Path,
    query: str,
    *,
    pipes: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build semantic handles for provider-owned Python policy rules."""
    del report, facts, project_root
    handles = [
        handle for handle in _policy_handles() if _matches_policy_query(handle, query)
    ]
    owner_paths = _handle_owner_paths(handles)
    test_paths = _handle_test_paths(handles)
    hits = [
        path_hit(path, path, kind="policy", score=5, reason="policy-handle")
        for path in owner_paths
    ]
    return {
        "header": header(
            "policy",
            {
                "q": query,
                "handle": len(handles),
                "owner": len(owner_paths),
                "tests": len(test_paths),
                "pipes": list(pipes),
            },
        ),
        "semanticHandles": handles,
        "hits": hits,
        "nextActions": _policy_next_actions(owner_paths, test_paths),
        "queryCoverage": [
            {
                "value": query,
                "kind": "custom",
                "selector": "exact",
                "status": "hit" if handles else "miss",
                "hitCount": len(handles),
                "ownerPaths": owner_paths,
                "fields": {"selectedHits": len(handles)},
            }
        ],
        "searchSynthesis": {
            "algorithm": "policy-handle-catalog",
            "scope": "policy",
            "summary": (
                "resolved provider-owned policy handles"
                if handles
                else "no provider-owned policy handle matched query"
            ),
            "selectedOwners": len(owner_paths),
            "testFrontier": test_paths,
        },
        "notes": [] if handles else [{"kind": "policy-not-found", "message": query}],
    }


def _policy_handles() -> list[dict[str, Any]]:
    handles: list[dict[str, Any]] = []
    handles.extend(
        _rule_handle(
            rule,
            owner_path=PROJECT_POLICY_CATALOG_OWNER,
            test_paths=PROJECT_POLICY_TEST_PATHS,
            domain="project-policy",
        )
        for rule in python_project_policy_rules()
    )
    handles.extend(
        _rule_handle(
            rule,
            owner_path=AGENT_POLICY_CATALOG_OWNER,
            test_paths=AGENT_POLICY_TEST_PATHS,
            domain="agent-policy",
        )
        for rule in python_agent_policy_rules()
    )
    return handles


def _rule_handle(
    rule: AspPythonRule,
    *,
    owner_path: str,
    test_paths: tuple[str, ...],
    domain: str,
) -> dict[str, Any]:
    rule_terms = _rule_query_terms(rule)
    return {
        "id": rule.rule_id,
        "kind": "policy-rule",
        "source": "provider-policy",
        "title": rule.title,
        "languageName": "python",
        "qualifiedName": f"{rule.pack_id}.{rule.rule_id}",
        "aliases": _rule_aliases(rule),
        "labels": sorted({domain, *rule.labels.values()}),
        "status": "advisory",
        "ownerPath": owner_path,
        "testPaths": list(test_paths),
        "locations": [{"path": owner_path}],
        "queryTerms": rule_terms,
        "fields": compact_fields(
            {
                "packId": rule.pack_id,
                "severity": rule.severity.value,
                "requirement": rule.requirement,
            }
        ),
    }


def _rule_aliases(rule: AspPythonRule) -> list[str]:
    return sorted(
        {
            rule.rule_id.lower(),
            rule.rule_id.replace("-", "_"),
            rule.rule_id.lower().replace("-", "_"),
            rule.pack_id,
            rule.labels.get("domain", ""),
        }
        - {""}
    )


def _rule_query_terms(rule: AspPythonRule) -> list[str]:
    return sorted(
        {
            rule.rule_id,
            rule.rule_id.lower(),
            rule.rule_id.replace("-", "_"),
            rule.pack_id,
            rule.title,
            rule.requirement,
            *rule.labels.values(),
        }
        - {""}
    )


def _matches_policy_query(handle: dict[str, Any], query: str) -> bool:
    needle = query.casefold().strip()
    if not needle:
        return True
    haystack = [
        handle["id"],
        handle["title"],
        handle.get("qualifiedName", ""),
        *handle.get("aliases", []),
        *handle.get("labels", []),
        *handle.get("queryTerms", []),
        *(str(value) for value in handle.get("fields", {}).values()),
    ]
    return any(needle in value.casefold() for value in haystack if value)


def _handle_owner_paths(handles: list[dict[str, Any]]) -> list[str]:
    return _dedupe(
        [
            path
            for handle in handles
            for path in (
                handle.get("implementationOwnerPath"),
                handle.get("ownerPath"),
            )
            if isinstance(path, str)
        ]
    )


def _handle_test_paths(handles: list[dict[str, Any]]) -> list[str]:
    return _dedupe(
        [
            path
            for handle in handles
            for path in handle.get("testPaths", [])
            if isinstance(path, str)
        ]
    )


def _policy_next_actions(
    owner_paths: list[str],
    test_paths: list[str],
) -> list[dict[str, str]]:
    actions = [{"kind": "owner", "target": path} for path in owner_paths]
    actions.extend({"kind": "tests", "target": path} for path in test_paths)
    return actions[:8]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
