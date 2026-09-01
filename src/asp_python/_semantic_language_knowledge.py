"""Knowledge-axis search descriptors for the Python semantic-language provider."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

_PYTHON_LANGUAGE_ID = "python"


def python_knowledge_search_view_descriptors() -> list[dict[str, Any]]:
    """Return provider-owned language and ecosystem knowledge search views."""

    return [
        _view(
            "env",
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-project-environment-facts"),
            ],
        ),
        _view(
            "runtime-source",
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-runtime-source-frontier"),
            ],
        ),
        _view(
            "lang",
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-language-semantics-facts"),
            ],
        ),
        _view(
            "std",
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-standard-api-facts"),
            ],
        ),
        _view(
            "capability",
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-provider-capability-facts"),
            ],
        ),
        _view(
            "extension",
            requires_query=True,
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-ecosystem-extension-facts"),
            ],
        ),
        _view(
            "pattern",
            requires_query=True,
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-executable-pattern-facts"),
            ],
        ),
        _view(
            "compare",
            requires_query=True,
            capabilities=[
                _semantic("provider-knowledge-axis"),
                _python("python-semantic-comparison-facts"),
            ],
        ),
    ]


def _view(
    view: str,
    *,
    capabilities: Sequence[dict[str, str]],
    requires_query: bool = False,
) -> dict[str, Any]:
    return {
        "method": f"search/{view}",
        "command": "search",
        "view": view,
        "requiresQuery": requires_query,
        "acceptsStdin": False,
        "supportsPackageScope": True,
        "capabilities": list(capabilities),
    }


def _semantic(name: str) -> dict[str, str]:
    return _capability("semantic", name)


def _python(name: str) -> dict[str, str]:
    return _capability(_PYTHON_LANGUAGE_ID, name)


def _capability(namespace: str, name: str) -> dict[str, str]:
    return {"languageId": _PYTHON_LANGUAGE_ID, "namespace": namespace, "name": name}
