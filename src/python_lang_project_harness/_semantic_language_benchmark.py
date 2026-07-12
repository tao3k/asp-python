"""Provider-owned large-library benchmark invocation templates."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_QUERY_VIEWS = {
    "api",
    "public-external-types",
    "policy",
    "symbol",
    "callsite",
    "import",
    "pattern",
    "compare",
}


def python_search_benchmark_invocation(view: str) -> dict[str, Any]:
    """Return the parser-valid public search command for one registry view."""
    builder = _SPECIAL_VIEW_BUILDERS.get(view)
    if builder is not None:
        return builder()
    if view in {"dependency", "deps"}:
        return _seed_invocation(view, "{dependency}")
    if view in _QUERY_VIEWS:
        return _seed_invocation(view, "{query}")
    return _seed_invocation(view)


def _owner_invocation() -> dict[str, Any]:
    return _seed_invocation("owner", "{owner}", "items", "--query", "{query}")


def _lexical_invocation() -> dict[str, Any]:
    return _seed_invocation("lexical", "--query", "{query}", "--query", "{dependency}")


def _tests_invocation() -> dict[str, Any]:
    return _seed_invocation("tests", "{owner}")


def _reasoning_invocation() -> dict[str, Any]:
    return _seed_invocation(
        "reasoning",
        "query-deps",
        "--query",
        "{query}",
        "--dependency",
        "{dependency}",
    )


def _ingest_invocation() -> dict[str, Any]:
    return {
        **_seed_invocation("ingest"),
        "stdinTemplate": "{owner}:1:{query}\\n",
    }


def _semantic_facts_invocation() -> dict[str, Any]:
    return {
        "args": ["search", "semantic-facts", "{query}", *_workspace(), "--json"],
        "expectsJson": True,
        "maxElapsedMs": 15_000,
    }


def _extension_invocation() -> dict[str, Any]:
    return _seed_invocation("extension", "{dependency}")


def _public_external_types_invocation() -> dict[str, Any]:
    return _seed_invocation("public-external-types", "{dependency}")


def _policy_invocation() -> dict[str, Any]:
    return _seed_invocation("policy", "PY-AGENT-POLICY-001")


def _seed_invocation(view: str, *args: str) -> dict[str, Any]:
    return {
        "args": ["search", view, *args, *_workspace(), "--view", "seeds"],
        "expectsJson": False,
        "maxElapsedMs": 15_000,
    }


def _workspace() -> list[str]:
    return ["--workspace", "{workspace}"]


_SPECIAL_VIEW_BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "owner": _owner_invocation,
    "lexical": _lexical_invocation,
    "tests": _tests_invocation,
    "reasoning": _reasoning_invocation,
    "ingest": _ingest_invocation,
    "semantic-facts": _semantic_facts_invocation,
    "extension": _extension_invocation,
    "public-external-types": _public_external_types_invocation,
    "policy": _policy_invocation,
}
