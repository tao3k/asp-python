"""Decode the provider ProjectResolution ABI and render typed failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._project_resolution_graph import (
    ProjectResolutionError,
    resolve_project_resolution,
)

_REQUEST_SCHEMA_ID = "agent.semantic-protocols.provider-project-resolution-request"
_RESPONSE_SCHEMA_ID = "agent.semantic-protocols.provider-project-resolution-response"


def resolve_project_resolution_request(
    request: dict[str, Any], *, cwd: Path
) -> dict[str, Any]:
    """Resolve one validated resident-runtime request without CLI dispatch."""

    request = _decode_request(json.dumps(request, separators=(",", ":")))
    try:
        return _response("resolved", scope=resolve_project_resolution(request, cwd=cwd))
    except ProjectResolutionError as error:
        return _failure(
            str(error),
            reason_kind=error.reason_kind,
            next_action=error.next_action,
        )
    except (ValueError, OSError) as error:
        return _failure(str(error))


def _decode_request(stdin: str) -> dict[str, Any]:
    try:
        request = json.loads(stdin)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"project-resolution request must be valid JSON: {error}"
        ) from error
    if not isinstance(request, dict):
        raise ValueError("project-resolution request must be a JSON object")
    if (
        request.get("schemaId") != _REQUEST_SCHEMA_ID
        or request.get("schemaVersion") != "1"
    ):
        raise ValueError("project-resolution request schema must be v1")
    if (
        request.get("languageId") != "python"
        or request.get("providerId") != "asp-python"
    ):
        raise ValueError(
            "project-resolution request provider identity does not match asp-python"
        )
    if request.get("candidateBase") != ".":
        raise ValueError("project-resolution request candidateBase must be .")
    generation = request.get("candidateGeneration")
    if not isinstance(generation, dict) or not isinstance(
        generation.get("digest"), str
    ):
        raise ValueError(
            "project-resolution request requires candidateGeneration.digest"
        )
    collection_scope = request.get("collectionScope")
    if not isinstance(collection_scope, dict):
        raise ValueError("project-resolution request collectionScope must be an object")
    collection_kind = collection_scope.get("kind")
    if collection_kind == "complete-generation":
        if set(collection_scope) != {"kind"}:
            raise ValueError("complete-generation collectionScope only accepts kind")
    elif collection_kind == "explicit-owners":
        owner_paths = collection_scope.get("ownerPaths")
        if not isinstance(owner_paths, list) or not owner_paths:
            raise ValueError("explicit-owners collectionScope requires ownerPaths")
        if not all(isinstance(path, str) and path for path in owner_paths):
            raise ValueError("explicit-owners ownerPaths must be non-empty text")
        if len(set(owner_paths)) != len(owner_paths) or any(
            path.startswith("/")
            or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            for path in owner_paths
        ):
            raise ValueError(
                "explicit-owners ownerPaths must be unique normalized workspace-relative paths"
            )
    else:
        raise ValueError(
            "project-resolution request collectionScope kind is unsupported"
        )
    entries = request.get("candidatePaths")
    if not isinstance(entries, list):
        raise ValueError("project-resolution request candidatePaths must be an array")
    if not isinstance(request.get("policyExclusions"), list):
        raise ValueError("project-resolution request policyExclusions must be an array")
    return request


def _response(
    state: str,
    *,
    scope: dict[str, Any] | None = None,
    failure: dict[str, str] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "schemaId": _RESPONSE_SCHEMA_ID,
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "state": state,
    }
    if scope is not None:
        response["scope"] = scope
    if failure is not None:
        response["failure"] = failure
    return response


def _failure(
    message: str,
    *,
    reason_kind: str = "project-entry-invalid",
    next_action: str = "send-valid-project-resolution-request",
) -> dict[str, Any]:
    if reason_kind == "provider-not-applicable":
        return _response("not-applicable")
    return _response(
        "failed",
        failure={
            "reasonKind": reason_kind,
            "message": message,
            "nextAction": next_action,
        },
    )
