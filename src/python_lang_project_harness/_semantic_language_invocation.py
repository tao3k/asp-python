"""Attach executable command templates to Python semantic-language descriptors."""

from typing import Any

from . import _semantic_language_ids as ids


def attach_semantic_language_invocations(
    descriptors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach one registry-v2 invocation to every method descriptor."""
    for descriptor in descriptors:
        benchmark = descriptor.get("benchmarkInvocation")
        if isinstance(benchmark, dict) and isinstance(benchmark.get("args"), list):
            invocation: dict[str, Any] = {
                "argv": [ids.PYTHON_BINARY, *benchmark["args"]]
            }
            if benchmark.get("stdinTemplate") is not None:
                invocation["stdinMode"] = "pipe-candidates"
            descriptor["invocation"] = invocation
        else:
            descriptor["invocation"] = _non_search_invocation(descriptor["method"])
    return descriptors


def _non_search_invocation(method: str) -> dict[str, list[str]]:
    invocations = {
        "query": [
            ids.PYTHON_BINARY,
            "query",
            "--catalog",
            "{query}",
            "--workspace",
            "{workspace}",
        ],
        "query/owner-items": [
            ids.PYTHON_BINARY,
            "query",
            "{owner}",
            "--term",
            "{query}",
            "--workspace",
            "{workspace}",
        ],
        "check/changed": [ids.PYTHON_BINARY, "check", "--changed", "{workspace}"],
        "check/full": [ids.PYTHON_BINARY, "check", "--full", "{workspace}"],
        "ast-patch/dry-run": [
            ids.PYTHON_BINARY,
            "ast-patch",
            "dry-run",
            "--packet",
            "{packet}",
        ],
        "evidence/graph": [
            ids.PYTHON_BINARY,
            "evidence",
            "graph",
            "--json",
            "{workspace}",
        ],
        "evidence/analyze": [
            ids.PYTHON_BINARY,
            "evidence",
            "analyze",
            "--json",
            "{workspace}",
        ],
        "agent/doctor": [ids.PYTHON_BINARY, "agent", "doctor", "--json"],
        "agent/guide": [ids.PYTHON_BINARY, "agent", "guide"],
    }
    return {"argv": invocations[method]}
