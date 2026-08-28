"""Black-box acceptance for the resident Python HTTP provider."""

from __future__ import annotations

import http.client
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
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


def _read_bootstrap(process: subprocess.Popen[str]) -> dict[str, object]:
    assert process.stdout is not None
    assert process.stderr is not None
    with ThreadPoolExecutor(max_workers=1) as executor:
        line = executor.submit(process.stdout.readline)
        try:
            bootstrap_line = line.result(timeout=2)
        except FutureTimeoutError as error:
            process.kill()
            _, stderr = process.communicate(timeout=2)
            raise AssertionError(
                f"Python provider exceeded the 2s bootstrap deadline: stderr={stderr!r}"
            ) from error
    if bootstrap_line:
        return json.loads(bootstrap_line)
    status = process.wait(timeout=2)
    stderr = process.stderr.read()
    raise AssertionError(
        f"Python provider exited before bootstrap: status={status} stderr={stderr!r}"
    )


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
    provider = shutil.which("asp-python")
    assert provider is not None, "uv project environment omitted asp-python"
    process = subprocess.Popen(
        [provider, "serve"],
        cwd=Path(__file__).parents[3],
        env=environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    bootstrap = _read_bootstrap(process)
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
