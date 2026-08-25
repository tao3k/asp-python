"""Own resident Python provider operations and runtime contract frames."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_REQUEST_SCHEMA_ID = "agent.semantic-protocols.provider-runtime-request-frame"
_RESPONSE_SCHEMA_ID = "agent.semantic-protocols.provider-runtime-response-frame"
_HEALTH_SCHEMA_ID = "agent.semantic-protocols.provider-runtime-contract-receipt"
_OPERATIONS = [
    {
        "operation": "projection-batch",
        "requestSchemaId": "https://schemas.agent-semantic-protocols.dev/provider-language-projection-batch-request.schema.json",
        "responseSchemaId": "https://schemas.agent-semantic-protocols.dev/provider-language-projection-batch-response.schema.json",
    },
    {
        "operation": "project-resolution",
        "requestSchemaId": "https://schemas.agent-semantic-protocols.dev/provider-project-resolution-request.schema.json",
        "responseSchemaId": "https://schemas.agent-semantic-protocols.dev/provider-project-resolution-response.schema.json",
    },
    {
        "operation": "query",
        "requestSchemaId": "https://agent-semantic-protocols.dev/schemas/provider-native-exact-request.v1.schema.json",
        "responseSchemaId": "https://agent-semantic-protocols.dev/schemas/provider-native-exact-response.v1.schema.json",
    },
]


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"resident Python provider omitted {name}")
    return value


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
        "operations": _OPERATIONS,
    }


def _execute(operation: str, payload: dict[str, Any], cwd: Path) -> dict[str, Any]:
    if operation == "projection-batch":
        from ._projection_batch import project_projection_batch

        return project_projection_batch(payload)
    if operation == "project-resolution":
        from ._project_resolution import resolve_project_resolution_request

        return resolve_project_resolution_request(payload, cwd=cwd)
    if operation == "query":
        from ._exact_source_projection import project_provider_native_exact_request

        return project_provider_native_exact_request(payload, cwd=cwd)
    raise RuntimeError(
        f"resident Python provider operation is not admitted: {operation}"
    )


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
        except (RuntimeError, ValueError) as execution_error:
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
