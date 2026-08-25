"""Render Python data-shape facts as graph-turbo nodes and edges."""

from __future__ import annotations

from typing import Any

from ._semantic_graph_fact_model import FieldFact
from ._semantic_graph_fact_render_fields import (
    render_collection_fact,
    render_collection_family,
    render_field_fact,
    render_type_fact,
)

LANGUAGE_ID = "python"
PROVIDER_ID = "asp-python"


def graph_payload(
    query: str, facts: list[FieldFact]
) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    collection_ids: set[str] = set()
    for fact in facts:
        field_id = field_id_for(fact)
        type_id = type_id_for(fact)
        locator = f"{fact.path}:{fact.line}:{fact.line}"
        fields = graph_fields(fact)
        nodes.append(field_node(fact, field_id, locator, fields))
        nodes.append(type_node(fact, type_id, locator, fields))
        edges.append({"source": field_id, "target": type_id, "relation": "has_type"})
        append_collection(nodes, edges, collection_ids, fact, field_id, type_id)
        if query:
            edges.append(
                {
                    "source": stable_id("query", query),
                    "target": field_id,
                    "relation": "matches",
                }
            )
    return {"nodes": nodes, "edges": edges}


def graph_fields(fact: FieldFact) -> dict[str, Any]:
    family = render_collection_family(fact.collection_kind)
    fields: dict[str, Any] = {
        "languageId": LANGUAGE_ID,
        "providerId": PROVIDER_ID,
        "semanticFactKind": "field",
        "provenance": "parser",
        "confidence": "exact",
        "freshness": "fresh",
        "containerName": fact.container_name,
        "fieldName": fact.field_name,
        "typeValue": fact.type_value,
        "elementShape": "collection" if fact.collection_kind else "scalar",
        "contextLocator": f"{fact.path}:{fact.context_start}:{fact.context_end}",
        "contextStartLine": fact.context_start,
        "contextEndLine": fact.context_end,
        "field": render_field_fact(fact, family),
    }
    if fact.collection_kind is not None:
        fields["collectionKind"] = fact.collection_kind
        fields["collectionFamily"] = family
        fields["collectionImpl"] = fact.collection_kind
    return fields


def field_node(
    fact: FieldFact,
    field_id: str,
    locator: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": field_id,
        "kind": "field",
        "role": "class-field",
        "value": f"{fact.field_name}: {fact.type_value}",
        "action": "code",
        "path": fact.path,
        "ownerPath": fact.path,
        "symbol": fact.field_name,
        "startLine": fact.line,
        "endLine": fact.line,
        "locator": locator,
        "matchText": f"{fact.container_name}.{fact.field_name}: {fact.type_value}",
        "fields": fields,
    }


def type_node(
    fact: FieldFact,
    type_id: str,
    locator: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    type_fields = {
        **fields,
        "semanticFactKind": "type",
        "type": render_type_fact(fact),
    }
    type_fields.pop("field", None)
    return {
        "id": type_id,
        "kind": "type",
        "role": "field-type",
        "value": fact.type_value,
        "action": "evidence",
        "path": fact.path,
        "ownerPath": fact.path,
        "symbol": fact.type_value.split("[", 1)[0],
        "startLine": fact.line,
        "endLine": fact.line,
        "locator": locator,
        "fields": type_fields,
    }


def append_collection(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    collection_ids: set[str],
    fact: FieldFact,
    field_id: str,
    type_id: str,
) -> None:
    if fact.collection_kind is None:
        return
    collection_id = f"collection:{fact.collection_kind}"
    if collection_id not in collection_ids:
        collection_ids.add(collection_id)
        nodes.append(
            {
                "id": collection_id,
                "kind": "collection",
                "role": "family",
                "value": fact.collection_kind,
                "action": "evidence",
                "symbol": fact.collection_kind,
                "fields": {
                    "languageId": LANGUAGE_ID,
                    "providerId": PROVIDER_ID,
                    "semanticFactKind": "collection",
                    "provenance": "parser",
                    "confidence": "exact",
                    "freshness": "fresh",
                    "collectionFamily": render_collection_family(fact.collection_kind),
                    "collectionImpl": fact.collection_kind,
                    "collectionKind": fact.collection_kind,
                    "collection": render_collection_fact(fact),
                },
            }
        )
    edges.append(
        {"source": field_id, "target": collection_id, "relation": "collection_of"}
    )
    edges.append(
        {"source": type_id, "target": collection_id, "relation": "collection_of"}
    )


def field_id_for(fact: FieldFact) -> str:
    return stable_id(
        "field",
        f"{fact.path}:{fact.container_name}:{fact.field_name}:{fact.line}",
    )


def type_id_for(fact: FieldFact) -> str:
    return stable_id(
        "type",
        f"{fact.path}:{fact.field_name}:{fact.type_value}:{fact.line}",
    )


def stable_id(kind: str, value: str) -> str:
    rendered = [kind, ":"]
    for character in value:
        if character.isalnum():
            rendered.append(character.lower())
        elif character in {"/", ".", "_", "-"}:
            rendered.append(character)
        else:
            rendered.append("-")
    return "".join(rendered).strip("-")
