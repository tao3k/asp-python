"""Shared ASP provider projection-batch transport for Python owners."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass

from ._callable_skeleton_projection import callable_skeleton_payload, collect_segments
from ._exact_projection_model import ExactSelector

_REQUEST_SCHEMA_ID = "asp.provider-language-projection-batch-request.v1"
_RESPONSE_SCHEMA_ID = "asp.provider-language-projection-batch-response.v1"
_IDENTITY_SCHEMA_ID = "asp.canonical-language-item-identity.v1"
_TRANSPORT = "framed-stdin-v1"


@dataclass(frozen=True, slots=True)
class _OwnerFrame:
    path: str
    digest: str
    source: bytes


def render_projection_batch(frame: bytes) -> str:
    """Decode one ASP frame and render the provider-owned projection response."""

    header, owners = _decode_frame(frame)
    projected = [_project_owner(owner, header) for owner in owners]
    response = {
        "schemaId": _RESPONSE_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": header["languageId"],
        "providerId": header["providerId"],
        "generationRootDigest": header["generationRootDigest"],
        "owners": projected,
    }
    return json.dumps(response, separators=(",", ":"), ensure_ascii=False)


def _decode_frame(frame: bytes) -> tuple[dict[str, object], list[_OwnerFrame]]:
    if len(frame) < 4:
        raise ValueError("projection batch frame is missing its header length")
    header_length = int.from_bytes(frame[:4], "big")
    header_end = 4 + header_length
    if header_end > len(frame):
        raise ValueError("projection batch header exceeds the input frame")
    header = json.loads(frame[4:header_end])
    if not isinstance(header, dict):
        raise ValueError("projection batch header must be an object")
    if (
        header.get("schemaId") != _REQUEST_SCHEMA_ID
        or header.get("schemaVersion") != "1"
        or header.get("languageId") != "python"
        or header.get("transport") != _TRANSPORT
        or not isinstance(header.get("parserIdentityDigest"), str)
        or not header.get("parserIdentityDigest")
        or not isinstance(header.get("queryPackDigest"), str)
        or not header.get("queryPackDigest")
    ):
        raise ValueError("projection batch request identity mismatch")
    owner_headers = header.get("owners")
    if not isinstance(owner_headers, list):
        raise ValueError("projection batch owners must be an array")
    cursor = header_end
    owners: list[_OwnerFrame] = []
    for raw_owner in owner_headers:
        if not isinstance(raw_owner, dict):
            raise ValueError("projection batch owner header must be an object")
        path = raw_owner.get("ownerPath")
        digest = raw_owner.get("sourceLeafDigest")
        byte_length = raw_owner.get("byteLength")
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(digest, str)
            or not digest
            or not isinstance(byte_length, int)
            or byte_length < 0
        ):
            raise ValueError("projection batch owner header is incomplete")
        owner_end = cursor + byte_length
        if owner_end > len(frame):
            raise ValueError(f"projection batch owner bytes are truncated: {path}")
        owners.append(_OwnerFrame(path, digest, frame[cursor:owner_end]))
        cursor = owner_end
    if cursor != len(frame):
        raise ValueError("projection batch frame has trailing bytes")
    return header, owners


def _project_owner(owner: _OwnerFrame, header: dict[str, object]) -> dict[str, object]:
    source = owner.source.decode("utf-8")
    tree = ast.parse(source, filename=owner.path)
    line_starts = _line_byte_starts(owner.source)
    items: list[dict[str, object]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            items.append(
                _project_item(owner, node, "function", (), line_starts, header)
            )
        elif isinstance(node, ast.ClassDef):
            items.append(_project_item(owner, node, "class", (), line_starts, header))
            scope = (("implementation-owner", "type", node.name),)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    items.append(
                        _project_item(
                            owner, child, "method", scope, line_starts, header
                        )
                    )
    return {
        "ownerPath": owner.path,
        "sourceLeafDigest": owner.digest,
        "items": items,
        "relations": [],
    }


def _project_item(
    owner: _OwnerFrame,
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    kind: str,
    scopes: tuple[tuple[str, str, str], ...],
    line_starts: list[int],
    header: dict[str, object],
) -> dict[str, object]:
    start = line_starts[node.lineno - 1] + node.col_offset
    end = line_starts[node.end_lineno - 1] + node.end_col_offset
    scope_path = "".join(
        f"/scope/{relation}/{scope_kind}/{symbol}"
        for relation, scope_kind, symbol in scopes
    )
    selector = f"python://{owner.path}#item/{kind}/{node.name}{scope_path}"
    projections: list[dict[str, object]] = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        exact_selector = ExactSelector(
            requested=selector,
            root=selector,
            owner_path=owner.path,
            kind=kind,
            symbol=node.name,
            segment_kind=None,
            segment_identity=None,
        )
        projection_request = {
            "generationIdentityDigest": header["generationRootDigest"],
            "parserIdentityDigest": header["parserIdentityDigest"],
            "queryPackDigest": header["queryPackDigest"],
        }
        projections.append(
            {
                "projectionKind": "callable-skeleton",
                "payload": callable_skeleton_payload(
                    projection_request,
                    exact_selector,
                    node,
                    collect_segments(node, line_starts),
                    start,
                    end,
                ),
            }
        )
    return {
        "itemId": f"item:{selector}",
        "ownerId": f"owner:{owner.path}",
        "kind": kind,
        "name": node.name,
        "selector": selector,
        "sourceByteStart": start,
        "sourceByteEnd": end,
        "identity": {
            "schemaId": _IDENTITY_SCHEMA_ID,
            "schemaVersion": "1",
            "languageId": "python",
            "kind": kind,
            "symbol": node.name,
            "scopes": [
                {"relation": relation, "kind": scope_kind, "symbol": symbol}
                for relation, scope_kind, symbol in scopes
            ],
        },
        "projections": projections,
    }


def _line_byte_starts(source: bytes) -> list[int]:
    starts = [0]
    starts.extend(index + 1 for index, byte in enumerate(source) if byte == 0x0A)
    return starts
