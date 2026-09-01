"""Shared ASP provider projection-batch transport for Python owners."""

from __future__ import annotations

import ast
import base64
import binascii
from dataclasses import dataclass

from ._callable_skeleton_projection import callable_skeleton_payload, collect_segments
from ._exact_projection_model import parse_selector

_REQUEST_SCHEMA_ID = (
    "agent.semantic-protocols.provider-language-projection-batch-request"
)
_RESPONSE_SCHEMA_ID = (
    "agent.semantic-protocols.provider-language-projection-batch-response"
)
_IDENTITY_SCHEMA_ID = "agent.semantic-protocols.canonical-language-item-identity"


@dataclass(frozen=True, slots=True)
class _OwnerFrame:
    path: str
    digest: str
    source: bytes


def project_projection_batch(request: dict[str, object]) -> dict[str, object]:
    """Project one structured resident-runtime request with the native AST."""

    owners, _auxiliary_owners = _decode_request(request)
    projected = [_project_owner(owner, request) for owner in owners]
    response = {
        "schemaId": _RESPONSE_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": request["languageId"],
        "providerId": request["providerId"],
        "generationRootDigest": request["generationRootDigest"],
        "owners": projected,
    }
    return response


def _decode_request(
    request: dict[str, object],
) -> tuple[list[_OwnerFrame], list[_OwnerFrame]]:
    if (
        request.get("schemaId") != _REQUEST_SCHEMA_ID
        or request.get("schemaVersion") != "1"
        or request.get("languageId") != "python"
        or not isinstance(request.get("parserIdentityDigest"), str)
        or not request.get("parserIdentityDigest")
        or not isinstance(request.get("queryPackDigest"), str)
        or not request.get("queryPackDigest")
    ):
        raise ValueError("projection batch request identity mismatch")
    owners = _decode_owners(request.get("owners"), "owners")
    auxiliary_owners = _decode_owners(
        request.get("auxiliaryOwners", []), "auxiliaryOwners"
    )
    paths = [owner.path for owner in (*owners, *auxiliary_owners)]
    if len(paths) != len(set(paths)):
        raise ValueError("projection batch owner paths must be unique")
    return owners, auxiliary_owners


def _decode_owners(value: object, field: str) -> list[_OwnerFrame]:
    if not isinstance(value, list):
        raise ValueError(f"projection batch {field} must be an array")
    owners: list[_OwnerFrame] = []
    for raw_owner in value:
        if not isinstance(raw_owner, dict):
            raise ValueError("projection batch owner must be an object")
        path = raw_owner.get("ownerPath")
        digest = raw_owner.get("sourceLeafDigest")
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(digest, str)
            or not digest
        ):
            raise ValueError("projection batch owner is incomplete")
        source_encoding = raw_owner.get("sourceEncoding")
        source_text = raw_owner.get("sourceText")
        source_bytes_base64 = raw_owner.get("sourceBytesBase64")
        if (
            source_encoding == "utf8"
            and isinstance(source_text, str)
            and source_bytes_base64 is None
        ):
            source = source_text.encode("utf-8")
        elif (
            source_encoding == "base64"
            and source_text is None
            and isinstance(source_bytes_base64, str)
        ):
            try:
                source = base64.b64decode(source_bytes_base64, validate=True)
            except (binascii.Error, ValueError) as error:
                raise ValueError("projection batch owner base64 is invalid") from error
        else:
            raise ValueError("projection batch owner source encoding mismatch")
        owners.append(_OwnerFrame(path, digest, source))
    return owners


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
        exact_selector = parse_selector(selector)
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
