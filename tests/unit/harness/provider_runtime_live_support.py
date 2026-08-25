"""Shared black-box HTTP corpus helpers for the resident Python provider."""

from __future__ import annotations

import base64
import http.client
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import SplitResult

from python_lang_project_harness._runtime import _response_frame


def environment() -> dict[str, str]:
    return {
        **os.environ,
        "ASP_PROVIDER_ARTIFACT_DIGEST": "blake3-256:" + "a" * 64,
        "ASP_PROVIDER_REGISTRATION_DIGEST": "sha256:" + "b" * 64,
        "ASP_PROVIDER_RUNTIME_CONTRACT_DIGEST": "blake3-256:" + "c" * 64,
        "ASP_PROVIDER_ID": "asp-python",
        "ASP_PROVIDER_LANGUAGE_ID": "python",
        "ASP_CLIENT_SERVER_HOST": "127.0.0.1:0",
    }


def post(connection: http.client.HTTPConnection, path: str, value: object) -> dict:
    body = json.dumps(value, separators=(",", ":")).encode()
    connection.request("POST", path, body, {"content-type": "application/json"})
    response = connection.getresponse()
    payload = json.loads(response.read())
    assert response.status == 200, payload
    return payload


def projection_payload(
    source: str = "def greet(name: str) -> str:\n    return name\n",
) -> dict:
    return {
        "schemaId": "agent.semantic-protocols.provider-language-projection-batch-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "workspaceIdentity": "workspace-python-live-corpus",
        "generationRootDigest": "blake3-256:generation-python-live-corpus",
        "parserIdentityDigest": "blake3-256:parser-python-live-corpus",
        "queryPackDigest": "blake3-256:query-python-live-corpus",
        "owners": [
            {
                "ownerPath": "src/example.py",
                "sourceLeafDigest": "blake3-256:owner-python-live-corpus",
                "sourceEncoding": "utf8",
                "sourceText": source,
            }
        ],
    }


def frame(request_id: str, operation: str, payload: dict) -> dict:
    return {
        "schemaId": "agent.semantic-protocols.provider-runtime-request-frame",
        "schemaVersion": "1",
        "requestId": request_id,
        "operation": operation,
        "payload": payload,
    }


def assert_projection_and_query(connection: http.client.HTTPConnection) -> None:
    projected = post(
        connection,
        "/v1/provider-runtime",
        frame("projection-1", "projection-batch", projection_payload()),
    )
    assert projected["outcome"] == "ready"
    assert projected["payload"]["owners"][0]["items"][0]["name"] == "greet"
    source = b"def greet(name: str) -> str:\n    return name\n"
    payload = {
        "schemaId": "agent.semantic-protocols.provider-native-exact-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "structuralSelector": "python://src/example.py#item/function/greet",
        "ownerPath": "src/example.py",
        "projectionKind": "source",
        "generationIdentityDigest": "a" * 64,
        "parserIdentityDigest": "b" * 64,
        "queryPackDigest": "c" * 64,
        "sourceDigest": "d" * 64,
        "sourceByteLength": len(source),
        "sourceEncoding": "base64",
        "sourceBytesBase64": base64.b64encode(source).decode(),
        "transport": "stdin-json",
    }
    queried = post(
        connection, "/v1/provider-runtime", frame("query-1", "query", payload)
    )
    assert queried["outcome"] == "ready"
    assert queried["payload"]["projectionText"].startswith("def greet")


def assert_streamed_corpus(connection: http.client.HTTPConnection) -> None:
    source = "#" + ("x" * (900 * 1024)) + "\ndef greet():\n    return 1\n"
    request = json.dumps(
        frame("stream-1", "projection-batch", projection_payload(source)),
        separators=(",", ":"),
    )
    chunks = [request[i : i + 128 * 1024] for i in range(0, len(request), 128 * 1024)]
    for index, chunk in enumerate(chunks):
        response = post(
            connection,
            "/v1/provider-runtime-stream",
            {
                "schemaId": "agent.semantic-protocols.provider-runtime-request-stream-frame",
                "schemaVersion": "1",
                "streamId": "stream-1",
                "frameIndex": index,
                "frameCount": len(chunks),
                "requestChunk": chunk,
            },
        )
        assert response["outcome" if index + 1 == len(chunks) else "state"] == (
            "ready" if index + 1 == len(chunks) else "accepted"
        )


def assert_concurrent_corpus(endpoint: SplitResult) -> None:
    def request(index: int) -> str:
        peer = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=2)
        try:
            return post(
                peer,
                "/v1/provider-runtime",
                frame(f"parallel-{index}", "projection-batch", projection_payload()),
            )["outcome"]
        finally:
            peer.close()

    with ThreadPoolExecutor(max_workers=16) as executor:
        assert set(executor.map(request, range(32))) == {"ready"}


def latency_receipt(connection: http.client.HTTPConnection) -> str:
    for index in range(16):
        post(
            connection,
            "/v1/provider-runtime",
            frame(f"warm-{index}", "projection-batch", projection_payload()),
        )
    loopback = []
    for index in range(128):
        started = time.perf_counter_ns()
        response = post(
            connection,
            "/v1/provider-runtime",
            frame(f"sample-{index}", "projection-batch", projection_payload()),
        )
        loopback.append((time.perf_counter_ns() - started) // 1000)
        assert response["outcome"] == "ready"
    service = []
    for index in range(256):
        started = time.perf_counter_ns()
        response = _response_frame(
            frame(f"service-{index}", "projection-batch", projection_payload()),
            Path("."),
        )
        service.append((time.perf_counter_ns() - started) // 1000)
        assert response["outcome"] == "ready"
    service_p99, loopback_p99 = percentile(service, 99), percentile(loopback, 99)
    assert service_p99 < 1_000
    return f"[provider-live-corpus] schemaVersion=1 provider=asp-python owners=1 samples=128 serviceP99Micros={service_p99} loopbackP99Micros={loopback_p99}"


def percentile(samples: list[int], value: int) -> int:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, (len(ordered) * value) // 100)]
