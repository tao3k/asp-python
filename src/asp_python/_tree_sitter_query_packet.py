"""Packet and compact rendering for Python tree-sitter-compatible queries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import _semantic_language_ids as ids
from ._tree_sitter_query_catalog import (
    PYTHON_TREE_SITTER_GRAMMAR_ID,
    PYTHON_TREE_SITTER_GRAMMAR_PROFILE_PATH,
    PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION,
    grammar_profile_source,
)
from ._tree_sitter_query_model import (
    SUPPORTED_TREE_SITTER_QUERY_NODES,
    SyntaxQueryProjection,
    SyntaxQueryRow,
    SyntaxQuerySelector,
    fingerprint,
    syntax_line_locator,
)
from ._tree_sitter_query_packet_rows import (
    _syntax_query_matches_json,
    _syntax_query_native_fact_refs,
)


def syntax_query_packet(
    *,
    project_root: Path,
    query: dict[str, Any],
    terms: list[str],
    selector: SyntaxQuerySelector | None,
    code_output: bool,
    projection: SyntaxQueryProjection,
) -> dict[str, Any]:
    catalog_source = str(query["source"])
    catalog_fingerprint = f"python-default:{fingerprint(catalog_source)}"
    profile_fingerprint = f"python-default:{fingerprint(grammar_profile_source())}"
    query_identity = str(query["catalogId"] or "inline")
    artifact_stem = str(query["catalogId"] or f"inline-{fingerprint(catalog_source)}")
    return {
        "schemaId": ids.SEMANTIC_TREE_SITTER_QUERY_SCHEMA_ID,
        "schemaVersion": "1",
        "protocolId": ids.SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": ids.SEMANTIC_LANGUAGE_PROTOCOL_VERSION,
        "languageId": ids.PYTHON_LANGUAGE_ID,
        "providerId": ids.PYTHON_PROVIDER_ID,
        "method": "query",
        "projectRoot": str(project_root),
        "grammarId": PYTHON_TREE_SITTER_GRAMMAR_ID,
        "grammarProfileVersion": PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION,
        "sourceAuthority": "native-parser-adapter",
        "adapterMode": "native-projection",
        "compatibilityLevel": "native-only",
        "query": _query_object(query, terms, selector, code_output),
        "matches": _syntax_query_matches_json(projection.rows),
        "nativeFactRefs": _syntax_query_native_fact_refs(projection.rows),
        "truncated": projection.truncated,
        "cache": {
            "cacheStatus": "miss",
            "requestFingerprint": (
                "semantic-tree-sitter-query.v1:"
                f"python:{PYTHON_TREE_SITTER_GRAMMAR_ID}:{query_identity}:"
                f"{catalog_fingerprint}:{profile_fingerprint}"
            ),
            "generationId": (
                "python-tree-sitter-query:"
                f"{artifact_stem}:{PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION}"
            ),
            "artifactId": f"semantic-tree-sitter-query/{artifact_stem}.json",
            "artifactKind": "semantic-tree-sitter-query",
            "catalogFingerprint": catalog_fingerprint,
            "grammarProfileFingerprint": profile_fingerprint,
            "rawSourceStored": False,
        },
    }


def tree_sitter_query_compact_lines(
    query: dict[str, Any],
    terms: list[str],
    projection: SyntaxQueryProjection,
) -> str:
    lines: list[str] = []
    if not projection.rows:
        lines.extend(_miss_lines(query, terms, projection))
    for index, row in enumerate(projection.rows):
        if index > 0:
            lines.append("")
        lines.append(syntax_line_locator(row.path, row.start_line, row.end_line))
        lines.append(_capture_text(row))
    if projection.truncated:
        lines.append(
            "|syntax-query-truncated "
            f"rows={len(projection.rows)} total={projection.total_matches} "
            "next=narrow-query-or-combine-with-owner"
        )
    return "\n".join(lines)


def tree_sitter_query_code(rows: list[SyntaxQueryRow]) -> str:
    return "\n\n".join(row.item_code for row in rows if row.item_code)


def _capture_text(row: SyntaxQueryRow) -> str:
    if (
        row.capture.endswith(".name")
        or row.capture.endswith(".target")
        or row.capture.endswith(".method")
    ):
        return row.name
    if row.capture.endswith(".definition"):
        return row.item_code
    return next(
        (line.strip() for line in row.item_code.splitlines() if line.strip()),
        row.name,
    )


def _query_object(
    query: dict[str, Any],
    terms: list[str],
    selector: SyntaxQuerySelector | None,
    code_output: bool,
) -> dict[str, Any]:
    query_fields: dict[str, Any] = {
        "captures": list(query["captures"]),
        "nodeTypes": list(query["nodeTypes"]),
        "fields": list(query["fields"]),
        "predicates": [_predicate_json(predicate) for predicate in query["predicates"]],
        "unsupportedPredicates": [],
        "catalogCanonical": bool(query["catalogCanonical"]),
        "catalogEmbedded": bool(query["catalogEmbedded"]),
        "compilerBoundary": "python-ast-tokenize-symtable",
        "providerRuntimeCompiled": False,
        "codeOutput": code_output,
        "terms": terms,
    }
    if selector is not None:
        query_fields["selector"] = selector.display()
    query_object: dict[str, Any] = {
        "input": query["input"],
        "inputForm": query["inputForm"],
        "dialect": "tree-sitter-query",
        "grammarProfilePath": PYTHON_TREE_SITTER_GRAMMAR_PROFILE_PATH,
        "compiledSource": query["source"],
        "fields": query_fields,
    }
    if query["catalogId"] is not None:
        query_object["catalogId"] = query["catalogId"]
    if query["catalogPath"] is not None:
        query_object["catalogPath"] = query["catalogPath"]
    return query_object


def _predicate_json(predicate: Any) -> dict[str, Any]:
    return {
        "op": predicate.op,
        "capture": predicate.capture,
        "values": [
            {"kind": value.kind, "value": value.value} for value in predicate.values
        ],
    }


def _miss_lines(
    query: dict[str, Any],
    terms: list[str],
    projection: SyntaxQueryProjection,
) -> list[str]:
    term_field = f" terms={','.join(terms)}" if terms else ""
    captures = ",".join(query["captures"]) if query["captures"] else "none"
    lines = [
        "|syntax-query "
        f"inputForm={query['inputForm']} input={query['input']} "
        f"grammar={PYTHON_TREE_SITTER_GRAMMAR_ID} "
        f"grammarProfile={PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION} "
        "dialect=tree-sitter-query mode=native-parser-projection "
        f"matchStatus={projection.match_status()} match={projection.total_matches} "
        f"rows={len(projection.rows)} truncated={str(projection.truncated).lower()} "
        f"captureCount={len(query['captures'])} captures={captures}{term_field} "
        f"catalogCanonical={str(query['catalogCanonical']).lower()} "
        f"catalogEmbedded={str(query['catalogEmbedded']).lower()} "
        "sourceAuthority=native-parser compilerBoundary=python-ast-tokenize-symtable "
        "providerRuntimeCompiled=false"
    ]
    if projection.unsupported_nodes:
        lines.append(
            "|syntax-query-unsupported "
            f"nodes={','.join(projection.unsupported_nodes)} "
            f"supported={','.join(sorted(SUPPORTED_TREE_SITTER_QUERY_NODES))}"
        )
    return lines
