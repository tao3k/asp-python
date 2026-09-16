"""Own resident Python provider operations and runtime contract frames."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_REQUEST_SCHEMA_ID = "agent.semantic-protocols.provider-runtime-request-frame"
_RESPONSE_SCHEMA_ID = "agent.semantic-protocols.provider-runtime-response-frame"
_HEALTH_SCHEMA_ID = "agent.semantic-protocols.provider-runtime-contract-receipt"


def _project_projection(payload: dict[str, Any], _cwd: Path) -> dict[str, Any]:
    from ._projection_batch import project_projection_batch

    return project_projection_batch(payload)


def _resolve_project(payload: dict[str, Any], cwd: Path) -> dict[str, Any]:
    from ._project_resolution import resolve_project_resolution_request

    return resolve_project_resolution_request(payload, cwd=cwd)


def _query_exact_source(payload: dict[str, Any], cwd: Path) -> dict[str, Any]:
    from ._exact_source_projection import project_provider_native_exact_request

    return project_provider_native_exact_request(payload, cwd=cwd)


_OPERATION_HANDLERS = {
    "projection-batch": _project_projection,
    "project-resolution": _resolve_project,
    "query": _query_exact_source,
}


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"resident Python provider omitted {name}")
    return value


def _runtime_operations() -> list[dict[str, str]]:
    name = "ASP_PROVIDER_RUNTIME_OPERATIONS_JSON"
    try:
        operations = json.loads(_required_env(name))
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"resident Python provider received invalid {name}"
        ) from error
    if not isinstance(operations, list) or not all(
        isinstance(operation, dict) for operation in operations
    ):
        raise RuntimeError(f"resident Python provider received invalid {name}")
    operation_names = {operation.get("operation") for operation in operations}
    if operation_names != set(_OPERATION_HANDLERS) or len(operations) != len(
        operation_names
    ):
        raise RuntimeError(
            "resident Python provider runtime operations do not match supported handlers"
        )
    return operations


def _health() -> dict[str, Any]:
    return {
        "schemaId": _HEALTH_SCHEMA_ID,
        "schemaVersion": "1",
        "providerId": _required_env("ASP_PROVIDER_ID"),
        "languageId": _required_env("ASP_PROVIDER_LANGUAGE_ID"),
        "artifactDigest": _required_env("ASP_PROVIDER_ARTIFACT_DIGEST"),
        "registrationDigest": _required_env("ASP_PROVIDER_REGISTRATION_DIGEST"),
        "contractDigest": _required_env("ASP_PROVIDER_RUNTIME_CONTRACT_DIGEST"),
        "transport": "http-json",
        "operations": _runtime_operations(),
    }


def _execute(operation: str, payload: dict[str, Any], cwd: Path) -> dict[str, Any]:
    handler = _OPERATION_HANDLERS.get(operation)
    if handler is None:
        raise RuntimeError(
            f"resident Python provider operation is not admitted: {operation}"
        )
    return handler(payload, cwd)


def _response_frame(request: dict[str, Any], cwd: Path) -> dict[str, Any]:
    request_id = request.get("requestId")
    operation = request.get("operation")
    if set(request) != {
        "schemaId",
        "schemaVersion",
        "requestId",
        "operation",
        "payload",
    }:
        error = "provider runtime request fields drift"
    elif (
        request.get("schemaId") != _REQUEST_SCHEMA_ID
        or request.get("schemaVersion") != "1"
    ):
        error = "provider runtime request schema identity drift"
    elif not isinstance(request_id, str) or not request_id.strip():
        error = "provider runtime request identity is empty"
    elif not isinstance(operation, str) or not operation.strip():
        error = "provider runtime operation is empty"
    else:
        try:
            payload = request.get("payload")
            if not isinstance(payload, dict):
                raise RuntimeError("provider runtime payload is not an object")
            result = _execute(operation, payload, cwd)
        except (RuntimeError, SyntaxError, ValueError) as execution_error:
            error = str(execution_error)
        else:
            return {
                "schemaId": _RESPONSE_SCHEMA_ID,
                "schemaVersion": "1",
                "requestId": request_id,
                "outcome": "ready",
                "payload": result,
            }
    return {
        "schemaId": _RESPONSE_SCHEMA_ID,
        "schemaVersion": "1",
        "requestId": request_id if isinstance(request_id, str) else "",
        "outcome": "error",
        "error": error,
    }


def serve_provider_runtime(cwd: Path) -> int:
    """Serve the schema-driven HTTP runtime through its isolated transport owner."""

    from ._runtime_http import serve_provider_runtime_http

    return serve_provider_runtime_http(cwd, _health())
