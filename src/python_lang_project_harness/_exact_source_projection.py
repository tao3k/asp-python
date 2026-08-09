from __future__ import annotations

import ast
import base64
import json
from pathlib import Path
from typing import Any, TextIO

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
    flag_value,
    line_byte_offsets,
    node_byte_span,
    parse_selector,
    required_int,
    required_text,
)


def try_run_provider_native_exact(
    args: list[str] | tuple[str, ...],
    *,
    stdin: str,
    cwd: Path,
    stdout: TextIO,
    stderr: TextIO,
) -> int | None:
    if "--asp-exact-request-stdin" not in args:
        return None
    try:
        request = json.loads(stdin)
        packet = _project_request(args, request, cwd)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        stderr.write(f"provider-native exact query failed: {error}\n")
        return 2
    stdout.write(json.dumps(packet, separators=(",", ":"), sort_keys=True))
    stdout.write("\n")
    return 0


def _project_request(
    args: list[str] | tuple[str, ...],
    request: dict[str, Any],
    cwd: Path,
) -> dict[str, Any]:
    _validate_request_identity(args, request)
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


def _validate_request_identity(
    args: list[str] | tuple[str, ...], request: dict[str, Any]
) -> None:
    expected = {
        "schemaId": REQUEST_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "py-harness",
        "sourceEncoding": "base64",
        "transport": "stdin-json",
    }
    for field, value in expected.items():
        if request.get(field) != value:
            raise ValueError(f"exact request {field} must be {value}")
    for flag, field in (
        ("--asp-provider-id", "providerId"),
        ("--asp-parser-identity-digest", "parserIdentityDigest"),
        ("--asp-query-pack-digest", "queryPackDigest"),
    ):
        if flag_value(args, flag) != required_text(request, field):
            raise ValueError(f"exact request authority mismatch for {field}")
    if flag_value(args, "--selector") != required_text(request, "structuralSelector"):
        raise ValueError("exact request selector does not match CLI authority")
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
        "providerId": "py-harness",
        "projectionMode": projection_kind,
        "requestedStructuralSelector": selector.requested,
        "structuralSelector": selector.requested,
        "sourceContentDigest": required_text(request, "sourceDigest"),
        "sourceByteStart": byte_start,
        "sourceByteEnd": max(byte_start, byte_end - 1),
    }
    if projection_text is not None:
        packet["projectionText"] = projection_text
    if projection_payload is not None:
        packet["projectionPayload"] = projection_payload
    return packet
