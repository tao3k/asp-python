"""Schema registrations advertised by the Python semantic-language provider."""

from __future__ import annotations

from . import _semantic_language_ids as ids


def python_semantic_language_schemas() -> list[dict[str, str]]:
    """Return package-local schema registrations for agent doctor."""

    return [
        {
            "schemaId": ids.SEMANTIC_SEARCH_PACKET_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-search-packet.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_QUERY_PACKET_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-query-packet.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_SOURCE_LOCATION_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-source-location.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_TREE_SITTER_PROVENANCE_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-tree-sitter-provenance.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_GRAPH_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-graph.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_GRAPH_TURBO_REQUEST_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-graph-turbo-request.v1.schema.json",
        },
        {
            "schemaId": "agent.semantic-protocols.semantic-verification-receipt",
            "schemaVersion": "1",
            "path": "schemas/semantic-verification-receipt.v1.schema.json",
        },
        {
            "schemaId": "agent.semantic-protocols.semantic-behavior-snapshot",
            "schemaVersion": "1",
            "path": "schemas/semantic-behavior-snapshot.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_DETERMINISM_READINESS_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-determinism-readiness.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_DEV_COMMAND_LOG_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-dev-command-log.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_FORMAL_PROOF_PILOT_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-formal-proof-pilot.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_REVIEW_PACKET_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-review-packet.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_EVIDENCE_GRAPH_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-evidence-graph.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_ASSURANCE_CASE_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-assurance-case.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_AST_PATCH_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-ast-patch.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_AST_PATCH_RECEIPT_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-ast-patch-receipt.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_TREE_SITTER_QUERY_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-tree-sitter-query.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_TREE_SITTER_GRAMMAR_PROFILE_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-tree-sitter-grammar-profile.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_TYPE_SURFACE_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-type-surface.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_FACT_GRAPH_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-fact-graph.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_FACT_ONTOLOGY_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/semantic-fact-ontology.v1.schema.json",
        },
        {
            "schemaId": "agent.semantic-protocols.semantic-handle",
            "schemaVersion": "1",
            "path": "schemas/semantic-handle.v1.schema.json",
        },
        {
            "schemaId": ids.SEMANTIC_LANGUAGE_REGISTRY_ID,
            "schemaVersion": ids.SEMANTIC_LANGUAGE_REGISTRY_VERSION,
            "path": "schemas/semantic-language-registry.v1.schema.json",
        },
        {
            "schemaId": ids.PYTHON_CAPABILITIES_SCHEMA_ID,
            "schemaVersion": "1",
            "path": "schemas/python-semantic-capabilities.v1.schema.json",
        },
    ]
