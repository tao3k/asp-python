"""Own isolated HTTP JSON transport for the resident Python provider."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from typing import Any

from ._runtime import _required_env, _response_frame

_MAX_REQUEST_BYTES = 896 * 1024
_MAX_STREAMS = 64
_MAX_STREAM_FRAMES = 1024


class RequestStreams:
    """Isolate interleaved bounded request streams by ASP request identity."""

    def __init__(self) -> None:
        self._states: dict[str, tuple[int, int, list[str]]] = {}
        self._lock = Lock()

    def accept(
        self, frame: dict[str, Any], execute: Callable[[bytes], dict[str, Any]]
    ) -> dict[str, Any]:
        stream_id, frame_index, frame_count, chunk = self._validate(frame)
        with self._lock:
            state = self._states.get(stream_id)
            if state is None:
                if frame_index != 0:
                    raise RuntimeError("provider runtime request stream is absent")
                if len(self._states) >= _MAX_STREAMS:
                    raise RuntimeError(
                        "provider runtime request stream capacity exceeded"
                    )
                state = (frame_count, 0, [])
                self._states[stream_id] = state
            expected_count, expected_index, chunks = state
            if expected_count != frame_count or expected_index != frame_index:
                self._states.pop(stream_id, None)
                raise RuntimeError("provider runtime request stream order drift")
            chunks.append(chunk)
            if frame_index + 1 < frame_count:
                self._states[stream_id] = (frame_count, frame_index + 1, chunks)
                return self._ack(stream_id, frame_index)
            self._states.pop(stream_id, None)
            request = "".join(chunks).encode()
        return execute(request)

    @staticmethod
    def _validate(frame: dict[str, Any]) -> tuple[str, int, int, str]:
        stream_id = frame.get("streamId")
        index = frame.get("frameIndex")
        count = frame.get("frameCount")
        chunk = frame.get("requestChunk")
        if (
            set(frame)
            != {
                "schemaId",
                "schemaVersion",
                "streamId",
                "frameIndex",
                "frameCount",
                "requestChunk",
            }
            or frame.get("schemaId")
            != "agent.semantic-protocols.provider-runtime-request-stream-frame"
            or frame.get("schemaVersion") != "1"
            or not isinstance(stream_id, str)
            or not stream_id
            or not isinstance(index, int)
            or isinstance(index, bool)
            or not isinstance(count, int)
            or isinstance(count, bool)
            or not 0 <= index < count <= _MAX_STREAM_FRAMES
            or count <= 1
            or not isinstance(chunk, str)
        ):
            raise RuntimeError("provider runtime request stream identity drift")
        return stream_id, index, count, chunk

    @staticmethod
    def _ack(stream_id: str, frame_index: int) -> dict[str, Any]:
        return {
            "schemaId": "agent.semantic-protocols.provider-runtime-request-stream-ack",
            "schemaVersion": "1",
            "streamId": stream_id,
            "frameIndex": frame_index,
            "state": "accepted",
        }


class ProviderRuntimeHandler(BaseHTTPRequestHandler):
    """Serve one provider instance with per-request thread isolation."""

    server_version = "asp-python"
    protocol_version = "HTTP/1.1"
    runtime_cwd = Path(".")
    runtime_health: dict[str, Any] = {}
    streams = RequestStreams()

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _json(self, status: int, value: dict[str, Any]) -> None:
        body = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("connection", "keep-alive")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> bytes:
        try:
            length = int(self.headers.get("content-length", ""))
        except ValueError as error:
            raise RuntimeError("provider runtime content-length is invalid") from error
        if not 0 <= length <= _MAX_REQUEST_BYTES:
            raise RuntimeError("provider runtime request exceeds byte budget")
        body = self.rfile.read(length)
        if len(body) != length:
            raise RuntimeError("provider runtime request body is truncated")
        return body

    def _runtime_request(self, body: bytes) -> dict[str, Any]:
        request = json.loads(body)
        if not isinstance(request, dict):
            raise RuntimeError("provider runtime request is not an object")
        return _response_frame(request, self.runtime_cwd)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, self.runtime_health)
        else:
            self._json(404, {"error": "asp-client-server-route-not-found"})

    def do_POST(self) -> None:
        try:
            if self.path == "/v1/provider-runtime":
                response = self._runtime_request(self._body())
            elif self.path == "/v1/provider-runtime-stream":
                frame = json.loads(self._body())
                if not isinstance(frame, dict):
                    raise RuntimeError(
                        "provider runtime request stream is not an object"
                    )
                response = self.streams.accept(frame, self._runtime_request)
            elif self.path == "/shutdown":
                self._json(200, {"state": "draining"})
                Thread(target=self.server.shutdown, daemon=True).start()
                return
            else:
                self._json(404, {"error": "asp-client-server-route-not-found"})
                return
        except (RuntimeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            self._json(400, {"error": str(error)})
        else:
            self._json(200, response)


def _handler(cwd: Path, health: dict[str, Any]) -> type[ProviderRuntimeHandler]:
    return type(
        "BoundProviderRuntimeHandler",
        (ProviderRuntimeHandler,),
        {"runtime_cwd": cwd, "runtime_health": health, "streams": RequestStreams()},
    )


def _parse_host(value: str) -> tuple[str, int]:
    host, separator, port = value.rpartition(":")
    if not separator or not host or not port:
        raise RuntimeError(f"invalid ASP_CLIENT_SERVER_HOST: {value}")
    try:
        parsed_port = int(port)
    except ValueError as error:
        raise RuntimeError(f"invalid ASP_CLIENT_SERVER_HOST port: {value}") from error
    if not 0 <= parsed_port <= 65535:
        raise RuntimeError(f"invalid ASP_CLIENT_SERVER_HOST port: {value}")
    return host.removeprefix("[").removesuffix("]"), parsed_port


def serve_provider_runtime_http(cwd: Path, health: dict[str, Any]) -> int:
    """Publish bootstrap only after the loopback HTTP socket is bound."""

    server = ThreadingHTTPServer(
        _parse_host(_required_env("ASP_CLIENT_SERVER_HOST")), _handler(cwd, health)
    )
    server.daemon_threads = True
    host, port = server.server_address[:2]
    bootstrap = {
        "schemaId": "agent.semantic-protocols.asp-client-server-bootstrap",
        "schemaVersion": "1",
        "providerId": _required_env("ASP_PROVIDER_ID"),
        "languageId": _required_env("ASP_PROVIDER_LANGUAGE_ID"),
        "transport": "http-json",
        "state": "ready",
        "endpoint": f"http://{host}:{port}/",
    }
    sys.stdout.write(
        json.dumps(bootstrap, sort_keys=True, separators=(",", ":")) + "\n"
    )
    sys.stdout.flush()
    try:
        server.serve_forever(poll_interval=0.01)
    finally:
        server.server_close()
    return 0
