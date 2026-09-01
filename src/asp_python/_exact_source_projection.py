"""Execute resident exact-source projections with the native Python AST."""

from __future__ import annotations

import ast
import base64
from pathlib import Path
from typing import Any

from ._callable_skeleton_projection import (
    callable_skeleton_payload,
    collect_segments,
)
from ._exact_projection_model import (
    REQUEST_SCHEMA_ID,
    RESPONSE_SCHEMA_ID,
    ExactSelector,
    ProjectionSegment,
    find_function,
    line_byte_offsets,
    node_byte_span,
    parse_selector,
    required_int,
    required_text,
)


def project_provider_native_exact_request(
    request: dict[str, Any], *, cwd: Path
) -> dict[str, Any]:
    """Execute one exact projection through the resident provider boundary."""

    _validate_request(request)
    return _project_request(request, cwd)


def _project_request(request: dict[str, Any], cwd: Path) -> dict[str, Any]:
    selector = parse_selector(required_text(request, "structuralSelector"))
    if selector.owner_path != required_text(request, "ownerPath"):
        raise ValueError("exact request ownerPath does not match structuralSelector")
    source = base64.b64decode(
        required_text(request, "sourceBytesBase64"), validate=True
    )
    if len(source) != required_int(request, "sourceByteLength"):
        raise ValueError("exact request sourceByteLength does not match decoded bytes")
    tree = ast.parse(source.decode("utf-8"), filename=str(cwd / selector.owner_path))
    function = find_function(tree, selector)
    line_offsets = line_byte_offsets(source)
    root_start, root_end = node_byte_span(function, line_offsets)
    segments = collect_segments(function, line_offsets)
    projection_kind = required_text(request, "projectionKind")
    if projection_kind == "source":
        return _source_packet(request, selector, source, segments, root_start, root_end)
    if projection_kind != "callable-skeleton":
        raise ValueError("projectionKind must be source or callable-skeleton")
    if selector.segment_kind is not None:
        raise ValueError(
            "callable-skeleton projection requires a root callable selector"
        )
    payload = callable_skeleton_payload(
        request, selector, function, segments, root_start, root_end
    )
    return _projection_packet(
        request,
        selector,
        projection_kind="callable-skeleton",
        byte_start=root_start,
        byte_end=root_end,
        projection_payload=payload,
    )


def _source_packet(
    request: dict[str, Any],
    selector: ExactSelector,
    source: bytes,
    segments: list[ProjectionSegment],
    root_start: int,
    root_end: int,
) -> dict[str, Any]:
    selected_start, selected_end = root_start, root_end
    if selector.segment_kind is not None:
        selected = next(
            (
                segment
                for segment in segments
                if segment.kind == selector.segment_kind
                and f"ordinal-{segment.ordinal}" == selector.segment_identity
            ),
            None,
        )
        if selected is None:
            raise ValueError("exact descendant selector does not resolve")
        selected_start, selected_end = selected.byte_start, selected.byte_end
    return _projection_packet(
        request,
        selector,
        projection_kind="source",
        byte_start=selected_start,
        byte_end=selected_end,
        projection_text=source[selected_start:selected_end].decode("utf-8"),
    )


def _validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schemaId": REQUEST_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "sourceEncoding": "base64",
        "transport": "stdin-json",
    }
    for field, value in expected.items():
        if request.get(field) != value:
            raise ValueError(f"exact request {field} must be {value}")
    for field in (
        "generationIdentityDigest",
        "parserIdentityDigest",
        "queryPackDigest",
        "sourceDigest",
    ):
        required_text(request, field)


def _projection_packet(
    request: dict[str, Any],
    selector: ExactSelector,
    *,
    projection_kind: str,
    byte_start: int,
    byte_end: int,
    projection_text: str | None = None,
    projection_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "schemaId": RESPONSE_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "ownerPath": selector.owner_path,
        "projectionMode": projection_kind,
        "requestedStructuralSelector": selector.requested,
        "structuralSelector": selector.requested,
        "sourceContentDigest": required_text(request, "sourceDigest"),
        "sourceByteStart": byte_start,
        "sourceByteEnd": max(byte_start, byte_end - 1),
        "normalizedParserFacts": {
            "itemKind": selector.kind,
            "itemName": selector.symbol,
            "scopes": [
                {
                    "role": role,
                    "ownerKind": owner_kind,
                    "ownerName": owner_name,
                }
                for role, owner_kind, owner_name in selector.scopes
            ],
        },
    }
    if projection_text is not None:
        packet["projectionText"] = projection_text
    if projection_payload is not None:
        packet["projectionPayload"] = projection_payload
    return packet
