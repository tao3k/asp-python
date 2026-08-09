from __future__ import annotations

import ast
import base64
import binascii
import json
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import quote

from blake3 import blake3

from ._exact_projection_model import line_byte_offsets, node_byte_span

REQUEST_SCHEMA_ID = "agent.semantic-protocols.provider-native-owner-search-request"
RESPONSE_SCHEMA_ID = "agent.semantic-protocols.provider-native-owner-search-response"
SCHEMA_VERSION = "1"


def try_run_provider_native_owner(
    args: list[str] | tuple[str, ...],
    *,
    stdin: str,
    cwd: Path,
    stdout: TextIO,
    stderr: TextIO,
) -> int | None:
    del cwd
    if not args or args[0] != "owner-search-stdin":
        return None
    try:
        provider_id = _flag_value(args, "--asp-provider-id")
        if provider_id is None:
            raise ValueError("owner-search stdin requires --asp-provider-id")
        request = json.loads(stdin)
        if not isinstance(request, dict):
            raise ValueError("owner-search request must be a JSON object")
        source = _validate_request(request, provider_id)
        response = _project_owner(request, provider_id, source)
        stdout.write(json.dumps(response, separators=(",", ":"), sort_keys=True))
        return 0
    except (
        UnicodeDecodeError,
        ValueError,
        binascii.Error,
        json.JSONDecodeError,
    ) as error:
        stderr.write(f"{error}\n")
        return 2


def _validate_request(request: dict[str, Any], provider_id: str) -> bytes:
    expected_fields = {
        "schemaId",
        "schemaVersion",
        "languageId",
        "providerId",
        "workspaceIdentity",
        "providerWorkspaceIdentityDigest",
        "ownerPath",
        "sourceFingerprint",
        "sourceEncoding",
        "sourceBytesBase64",
        "projectionMode",
        "transport",
    }
    if set(request) != expected_fields:
        raise ValueError("owner-search request fields drift")
    if (
        request["schemaId"] != REQUEST_SCHEMA_ID
        or request["schemaVersion"] != SCHEMA_VERSION
        or request["languageId"] != "python"
        or request["providerId"] != provider_id
        or not _nonempty_text(request["workspaceIdentity"])
        or not _digest_text(request["providerWorkspaceIdentityDigest"])
        or not _nonempty_text(request["ownerPath"])
        or request["sourceEncoding"] != "base64"
        or request["projectionMode"] != "complete-owner"
        or request["transport"] != "stdin-json"
    ):
        raise ValueError("owner-search request identity or completeness drift")

    fingerprint = request["sourceFingerprint"]
    if not isinstance(fingerprint, dict) or set(fingerprint) != {
        "fileIdentity",
        "sizeBytes",
        "modifiedUnixNanos",
        "changeTimeUnixNanos",
        "contentDigest",
    }:
        raise ValueError("owner-search source fingerprint drift")
    if (
        not _nonempty_text(fingerprint["fileIdentity"])
        or not _nonnegative_int(fingerprint["sizeBytes"])
        or not _nonnegative_int(fingerprint["modifiedUnixNanos"])
        or not _nonnegative_int(fingerprint["changeTimeUnixNanos"])
        or not _digest_text(fingerprint["contentDigest"])
    ):
        raise ValueError("owner-search source fingerprint is incomplete")

    encoded = request["sourceBytesBase64"]
    if not isinstance(encoded, str):
        raise ValueError("owner-search source base64 must be text")
    source = base64.b64decode(encoded, validate=True)
    if len(source) != fingerprint["sizeBytes"]:
        raise ValueError("owner-search source size drift")
    if blake3(source).hexdigest() != fingerprint["contentDigest"]:
        raise ValueError("owner-search source content digest drift")
    source.decode("utf-8")
    return source


def _project_owner(
    request: dict[str, Any], provider_id: str, source: bytes
) -> dict[str, Any]:
    source_text = source.decode("utf-8")
    tree = ast.parse(source_text)
    offsets = line_byte_offsets(source)
    projections = _owner_projections(tree.body, request["ownerPath"], offsets, [])
    projections.sort(
        key=lambda projection: (
            projection["sourceByteStart"],
            projection["canonicalItemSelector"]["structuralSelector"],
        )
    )
    return {
        "schemaId": RESPONSE_SCHEMA_ID,
        "schemaVersion": SCHEMA_VERSION,
        "languageId": "python",
        "providerId": provider_id,
        "requestedOwnerPath": request["ownerPath"],
        "requestedProjectionMode": request["projectionMode"],
        "sourceContentDigest": request["sourceFingerprint"]["contentDigest"],
        "parsedOwnerCount": 1,
        "projectionCompleteness": "complete-owner",
        "projections": projections,
    }


def _function_projection(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    owner_path: str,
    offsets: list[int],
    scopes: list[dict[str, str]],
    item_kind: str,
) -> dict[str, Any]:
    byte_start, byte_end = node_byte_span(node, offsets)
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    signature = f"{prefix} {node.name}({ast.unparse(node.args)})"
    if node.returns is not None:
        signature += f" -> {ast.unparse(node.returns)}"
    selector = _canonical_item_selector(
        owner_path=owner_path,
        item_kind=item_kind,
        symbol=node.name,
        scopes=scopes,
    )
    return {
        "canonicalItemSelector": selector,
        "signature": signature,
        "captureName": "function_definition/name",
        "sourceByteStart": byte_start,
        "sourceByteEnd": byte_end,
    }


def _owner_projections(
    nodes: list[ast.stmt],
    owner_path: str,
    offsets: list[int],
    scopes: list[dict[str, str]],
) -> list[dict[str, Any]]:
    projections: list[dict[str, Any]] = []
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            byte_start, byte_end = node_byte_span(node, offsets)
            projections.append(
                {
                    "canonicalItemSelector": _canonical_item_selector(
                        owner_path=owner_path,
                        item_kind="class",
                        symbol=node.name,
                        scopes=scopes,
                    ),
                    "signature": f"class {node.name}",
                    "captureName": "class_definition/name",
                    "sourceByteStart": byte_start,
                    "sourceByteEnd": byte_end,
                }
            )
            projections.extend(
                _owner_projections(
                    node.body,
                    owner_path,
                    offsets,
                    [
                        *scopes,
                        {
                            "relation": "class-owner",
                            "kind": "class",
                            "symbol": node.name,
                        },
                    ],
                )
            )
            continue
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        item_kind = (
            "method"
            if scopes and scopes[-1]["relation"] == "class-owner"
            else "function"
        )
        projections.append(
            _function_projection(node, owner_path, offsets, scopes, item_kind)
        )
        projections.extend(
            _owner_projections(
                node.body,
                owner_path,
                offsets,
                [
                    *scopes,
                    {
                        "relation": "lexical-owner",
                        "kind": "function",
                        "symbol": node.name,
                    },
                ],
            )
        )
    return projections


def _canonical_item_selector(
    *,
    owner_path: str,
    item_kind: str,
    symbol: str,
    scopes: list[dict[str, str]],
) -> dict[str, Any]:
    identity_path = f"item/{_component(item_kind)}/{_component(symbol)}"
    identity_path += "".join(
        f"/scope/{_component(scope['relation'])}/{_component(scope['kind'])}/{_component(scope['symbol'])}"
        for scope in scopes
    )
    return {
        "schemaId": "asp.canonical-item-selector.v1",
        "schemaVersion": "1",
        "languageId": "python",
        "kind": item_kind,
        "symbol": symbol,
        "scopes": list(scopes),
        "structuralSelector": f"python://{owner_path}#{identity_path}",
    }


def _component(value: str) -> str:
    return quote(value, safe="-._~")


def _flag_value(args: list[str] | tuple[str, ...], flag: str) -> str | None:
    try:
        index = args.index(flag)
    except ValueError:
        return None
    if index + 1 >= len(args):
        return None
    return args[index + 1]


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _digest_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
