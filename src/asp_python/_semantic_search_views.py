"""Semantic-search view dispatcher for Python packets."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import header
from ._semantic_search_hits import api_hits, callsite_hits, symbol_hits
from ._semantic_search_model import MAX_SYMBOL_HITS, PythonSemanticSearchOptions
from ._semantic_search_public_external_types import public_external_types_payload
from ._semantic_search_view_core import owner_payload, prime_payload, workspace_payload
from ._semantic_search_view_deps_imports import dependency_payload, import_payload
from ._semantic_search_view_hits import (
    generic_hits_payload,
    tests_payload,
    text_payload,
)
from ._semantic_search_view_ingest import ingest_payload
from ._semantic_search_view_knowledge import knowledge_payload

if TYPE_CHECKING:
    from python_lang_parser import PythonReasoningTreeFacts

    from ._model import AspPythonReport


def payload_for_view(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    options: PythonSemanticSearchOptions,
) -> dict[str, Any]:
    """Dispatch one semantic-search view."""

    return _payload_for_view(report, facts, project_root, options)


def _payload_for_view(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    options: PythonSemanticSearchOptions,
) -> dict[str, Any]:
    """Dispatch one semantic-search view behind the thin public facade."""

    query = options.query or ""
    match options.view:
        case "workspace":
            return workspace_payload(report, facts, project_root)
        case "prime":
            return prime_payload(report, facts, project_root)
        case "owner":
            return owner_payload(
                report,
                facts,
                project_root,
                query,
                pipes=options.pipes,
                item_query=options.item_query,
            )
        case "dependency" | "deps":
            return dependency_payload(report, facts, project_root, query, options.view)
        case "api":
            hits = api_hits(report, facts, project_root, query)[:MAX_SYMBOL_HITS]
            return generic_hits_payload("api", hits, facts, project_root, query)
        case "public-external-types":
            return public_external_types_payload(report, facts, project_root, query)
        case "policy":
            from ._semantic_search_policy import policy_payload

            return policy_payload(
                report,
                facts,
                project_root,
                query,
                pipes=options.pipes,
            )
        case "symbol":
            hits = symbol_hits(report, project_root, query)[:MAX_SYMBOL_HITS]
            return generic_hits_payload("symbol", hits, facts, project_root, query)
        case "callsite":
            hits = callsite_hits(report, project_root, query)[:MAX_SYMBOL_HITS]
            return generic_hits_payload("callsite", hits, facts, project_root, query)
        case "import":
            return import_payload(report, facts, project_root, query)
        case "tests":
            return tests_payload(report, facts, project_root, query)
        case "lexical":
            return text_payload(report, facts, project_root, options)
        case "reasoning":
            from ._semantic_search_reasoning import reasoning_payload

            return reasoning_payload(report, facts, project_root, options)
        case (
            "env"
            | "runtime-source"
            | "lang"
            | "std"
            | "capability"
            | "extension"
            | "pattern"
            | "compare"
        ):
            return knowledge_payload(project_root, options)
        case "ingest":
            return ingest_payload(facts, project_root, options.stdin)
        case _:
            return {
                "header": header(
                    options.view, {"error": f"unknown view {options.view}"}
                )
            }
