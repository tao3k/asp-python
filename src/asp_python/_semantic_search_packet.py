"""Top-level semantic-search packet assembly for the Python provider."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import _semantic_language_ids as ids
from ._semantic_search_model import PythonSemanticSearchOptions
from ._semantic_search_views import payload_for_view
from .verification.facts import (
    verification_project_root,
    verification_reasoning_tree_facts,
)

if TYPE_CHECKING:
    from ._model import AspPythonReport


def build_python_semantic_search_packet(
    report: AspPythonReport,
    options: PythonSemanticSearchOptions,
) -> dict[str, Any]:
    """Build a language-neutral semantic-search packet from Python parser facts."""

    facts = verification_reasoning_tree_facts(report)
    project_root = verification_project_root(report)
    payload = payload_for_view(report, facts, project_root, options)
    packet = _base_python_search_packet(project_root, options, payload)
    _attach_query(packet, options)
    _attach_query_set(packet, options)
    _attach_package_name(packet, facts)
    _attach_reasoning_profiles(packet, options)
    _attach_runtime_cost(packet, options)
    _attach_payload_optionals(packet, payload)
    _attach_syntax_refs(packet, payload)
    return _normalize_packet_locations(packet)


def _attach_query(packet: dict[str, Any], options: PythonSemanticSearchOptions) -> None:
    if options.query is not None:
        packet["query"] = options.query


def _attach_query_set(
    packet: dict[str, Any], options: PythonSemanticSearchOptions
) -> None:
    query_terms = [
        {
            "value": term,
            "kind": "text",
            "selector": "lexical" if options.view == "lexical" else "exact",
        }
        for term in _normalized_query_set(options.query_set)
    ]
    if query_terms:
        packet["querySet"] = query_terms
        scope = (
            {"ownerPath": options.owner_path}
            if options.owner_path is not None
            else None
        )
        packet["queryComposition"] = {
            "mode": "query-set",
            "view": options.view,
            "selector": "lexical-set" if options.view == "lexical" else "exact-set",
            **({} if scope is None else {"scope": scope}),
            "merge": [
                "nodes",
                "edges",
                "owners",
                "hits",
                "typeSurfaces",
                "nextActions",
                "notes",
            ],
        }


def _attach_package_name(packet: dict[str, Any], facts: Any) -> None:
    if facts.project_metadata is not None and facts.project_metadata.project_name:
        packet["packageName"] = facts.project_metadata.project_name


def _attach_reasoning_profiles(
    packet: dict[str, Any], options: PythonSemanticSearchOptions
) -> None:
    if (options.render_mode or "both") in {"graph", "seeds", "both", "facts"}:
        from ._semantic_search_profiles import python_reasoning_profiles

        packet["reasoningProfiles"] = python_reasoning_profiles()


def _attach_runtime_cost(
    packet: dict[str, Any], options: PythonSemanticSearchOptions
) -> None:
    if options.runtime_cost is not None:
        packet["runtimeCost"] = options.runtime_cost
        packet["notes"] = [
            *packet["notes"],
            {
                "kind": "runtime-prefilter",
                "message": str(options.runtime_cost.get("reason", "")),
                "fields": options.runtime_cost.get("fields", {}),
            },
        ]


def _attach_payload_optionals(packet: dict[str, Any], payload: dict[str, Any]) -> None:
    for optional_key in (
        "inputDetection",
        "packages",
        "items",
        "typeSurfaces",
        "semanticHandles",
        "queryCoverage",
        "ownerResolution",
        "runtimeCost",
        "searchSynthesis",
        "avoidNextActions",
    ):
        if payload.get(optional_key) is not None:
            packet[optional_key] = payload[optional_key]


def _attach_syntax_refs(packet: dict[str, Any], payload: dict[str, Any]) -> None:
    items = payload.get("items")
    if not isinstance(items, list):
        return

    from ._semantic_syntax_refs import (
        annotate_python_owner_item_syntax_refs,
        attach_python_syntax_refs,
    )

    syntax_refs = annotate_python_owner_item_syntax_refs(items)
    attach_python_syntax_refs(packet, syntax_refs)


def _base_python_search_packet(
    project_root: Any,
    options: PythonSemanticSearchOptions,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schemaId": ids.SEMANTIC_SEARCH_PACKET_SCHEMA_ID,
        "schemaVersion": "1",
        "protocolId": ids.SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": ids.SEMANTIC_LANGUAGE_PROTOCOL_VERSION,
        "languageId": ids.PYTHON_LANGUAGE_ID,
        "providerId": ids.PYTHON_PROVIDER_ID,
        "binary": ids.PYTHON_BINARY,
        "namespace": ids.PYTHON_PROVIDER_NAMESPACE,
        "method": f"search/{options.view}",
        "projectRoot": str(project_root),
        "view": options.view,
        "renderMode": options.render_mode or "both",
        "header": payload["header"],
        "nodes": payload.get("nodes", []),
        "edges": payload.get("edges", []),
        "owners": payload.get("owners", []),
        "hits": payload.get("hits", []),
        "findings": payload.get("findings", []),
        "nextActions": payload.get("nextActions", []),
        "notes": payload.get("notes", []),
    }


def _normalize_packet_locations(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_packet_locations(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized = {key: _normalize_packet_locations(item) for key, item in value.items()}
    line = normalized.pop("line", None)
    if "path" in normalized and isinstance(line, int):
        end_line = normalized.pop("endLine", None)
        normalized.pop("column", None)
        normalized.pop("endColumn", None)
        if not isinstance(end_line, int):
            end_line = line
        normalized["lineRange"] = f"{line}:{end_line}"
    return normalized


def _normalized_query_set(query_set: tuple[str, ...]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for raw_term in query_set:
        term = raw_term.strip()
        if not term or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return terms
