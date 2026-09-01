"""Typed reasoning entry payloads for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import header
from ._semantic_search_model import PythonSemanticSearchOptions
from ._semantic_search_owners import owners_for_paths
from ._semantic_search_view_core import owner_payload
from ._semantic_search_view_deps_imports import dependency_payload
from ._semantic_search_view_hits import tests_payload

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport


_OWNER_TESTS_RETURNS = ["covering-tests", "test-entrypoints", "fixtures"]
_OWNER_QUERY_RETURNS = ["items", "tests", "dependency-usage"]
_QUERY_DEPS_RETURNS = ["owners", "imports", "usage-tests"]


def reasoning_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    options: PythonSemanticSearchOptions,
) -> dict[str, Any]:
    """Build payloads for explicit graph reasoning entries."""

    profile = options.query or ""
    match profile:
        case "owner-tests":
            owner = _required(options.owner_path, "--owner", profile)
            payload = tests_payload(report, facts, project_root, owner)
            _ensure_owner_selector(payload, facts, project_root, owner)
            return _with_reasoning_header(
                payload,
                profile=profile,
                owner_path=owner,
                returns=_OWNER_TESTS_RETURNS,
            )
        case "owner-query":
            owner = _required(options.owner_path, "--owner", profile)
            query = _required(options.item_query, "--query", profile)
            payload = owner_payload(
                report,
                facts,
                project_root,
                owner,
                pipes=("items",),
                item_query=query,
            )
            return _with_reasoning_header(
                payload,
                profile=profile,
                owner_path=owner,
                query=query,
                returns=_OWNER_QUERY_RETURNS,
            )
        case "query-deps":
            query = _required(options.item_query, "--query", profile)
            dependency = _required(options.dependency, "--dependency", profile)
            dep_query = f"{dependency}::{query}"
            payload = dependency_payload(report, facts, project_root, dep_query, "deps")
            return _with_reasoning_header(
                payload,
                profile=profile,
                query=query,
                dependency=dependency,
                returns=_QUERY_DEPS_RETURNS,
            )
        case _:
            raise ValueError(
                "unknown reasoning profile: "
                f"{profile}; expected owner-tests, owner-query, or query-deps"
            )


def _with_reasoning_header(
    payload: dict[str, Any],
    *,
    profile: str,
    returns: list[str],
    owner_path: str | None = None,
    query: str | None = None,
    dependency: str | None = None,
) -> dict[str, Any]:
    payload["header"] = header(
        "reasoning",
        {
            "profile": profile,
            "ownerPath": owner_path,
            "query": query,
            "dependency": dependency,
            "returns": returns,
            "owner": len(payload.get("owners", [])),
            "hit": len(payload.get("hits", [])),
            "item": len(payload.get("items", [])),
        },
    )
    return payload


def _ensure_owner_selector(
    payload: dict[str, Any],
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    owner_path: str,
) -> None:
    existing_paths = {owner["path"] for owner in payload.get("owners", [])}
    if owner_path in existing_paths:
        return
    payload["owners"] = [
        *payload.get("owners", []),
        *owners_for_paths(facts, project_root, [owner_path]),
    ]


def _required(value: str | None, flag: str, profile: str) -> str:
    if value is None or not value:
        raise ValueError(f"search reasoning {profile} requires {flag}")
    return value
