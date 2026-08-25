"""Black-box acceptance for the resident Python HTTP provider."""

from __future__ import annotations

import http.client
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from provider_runtime_live_support import (
    assert_concurrent_corpus,
    assert_projection_and_query,
    assert_streamed_corpus,
    environment,
    frame,
    latency_receipt,
    post,
)

from python_lang_project_harness._runtime import _health, _response_frame


def test_resident_runtime_publishes_manifest_operations_and_structured_frames(
    monkeypatch: object,
) -> None:
    for name, value in environment().items():
        monkeypatch.setenv(name, value)  # type: ignore[attr-defined]
    health = _health()
    assert (
        health["schemaId"]
        == "agent.semantic-protocols.provider-runtime-contract-receipt"
    )
    assert health["transport"] == "http-json"
    assert [operation["operation"] for operation in health["operations"]] == [
        "projection-batch",
        "project-resolution",
        "query",
    ]
    response = _response_frame(frame("request-1", "not-admitted", {}), Path("."))
    assert response["outcome"] == "error"
    assert (
        response["error"]
        == "resident Python provider operation is not admitted: not-admitted"
    )


def test_http_json_live_corpus_stream_query_concurrency_and_latency() -> None:
    process = subprocess.Popen(
        [sys.executable, "-m", "python_lang_project_harness", "serve"],
        cwd=Path(__file__).parents[3],
        env=environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    bootstrap = json.loads(process.stdout.readline())
    assert (
        bootstrap["schemaId"] == "agent.semantic-protocols.asp-client-server-bootstrap"
    )
    assert (bootstrap["providerId"], bootstrap["languageId"], bootstrap["state"]) == (
        "asp-python",
        "python",
        "ready",
    )
    endpoint = urlsplit(bootstrap["endpoint"])
    connection = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=2)
    try:
        connection.request("GET", "/health")
        health_response = connection.getresponse()
        assert health_response.status == 200
        assert json.loads(health_response.read())["providerId"] == "asp-python"
        assert_projection_and_query(connection)
        assert_streamed_corpus(connection)
        assert_concurrent_corpus(endpoint)
        print(latency_receipt(connection))
        assert post(connection, "/shutdown", {}) == {"state": "draining"}
        assert process.wait(timeout=2) == 0
    finally:
        connection.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)
