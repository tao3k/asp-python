"""Search method descriptors for the Python semantic-language provider."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

_PYTHON_LANGUAGE_ID = "python"


def python_search_view_descriptors() -> list[dict[str, Any]]:
    """Return implemented Python search view descriptors."""

    descriptors = [
        _view(
            "workspace",
            capabilities=[
                _semantic("workspace-router"),
                _python("python-package-root-search"),
            ],
        ),
        _view(
            "workspace-scope",
            capabilities=[
                _semantic("workspace-candidate-admission"),
                _python("python-package-manager-workspace-scope"),
            ],
        ),
        _view(
            "prime",
            capabilities=[
                _semantic("package-prime-map"),
                _python("python-reasoning-tree-prime"),
                _python("python-entry-point-search"),
            ],
        ),
        _view(
            "owner",
            requires_query=True,
            accepted_pipes=["items"],
            capabilities=[
                _semantic("reasoning-owner-search"),
                _python("parser-visible-module-owner-search"),
                _python("python-owner-item-query"),
                _python("pytest-test-owner-search"),
                _semantic("path-owner-fallback"),
            ],
            fallbacks=[
                {
                    "name": "owner-top-items",
                    "trigger": "item-query-miss",
                    "appliesToPipes": ["items"],
                    "maxItems": 4,
                }
            ],
            ingest_required_for=[_ingest("non-parser-path")],
        ),
        _view(
            "dependency",
            requires_query=True,
            capabilities=[
                _semantic("dependency-manifest-search"),
                _python("dependency-local-usage-search"),
            ],
        ),
        _view(
            "deps",
            requires_query=True,
            capabilities=[
                _semantic("dependency-manifest-search"),
                _python("dependency-local-usage-search"),
                _semantic("dependency-version-scope"),
                _python("dependency-api-token-usage-search"),
            ],
        ),
        _view(
            "api",
            requires_query=True,
            capabilities=[
                _python("exported-api-shape-search"),
                _python("public-function-api-shape-search"),
                _python("public-data-api-shape-search"),
                _semantic("dependency-version-scope"),
            ],
            ingest_required_for=[_ingest("external-api-docs")],
        ),
        _view(
            "public-external-types",
            requires_query=True,
            capabilities=[
                _semantic("dependency-manifest-search"),
                _python("public-external-type-search"),
                _python("public-api-type-text-search"),
            ],
        ),
        _view(
            "policy",
            requires_query=True,
            accepted_pipes=["owner", "tests"],
            capabilities=[
                _semantic("policy-rule-handle-search"),
                _python("python-project-policy-rule-handle-search"),
                _python("python-agent-policy-rule-handle-search"),
            ],
        ),
        _view(
            "symbol",
            requires_query=True,
            capabilities=[_python("symbol-definition-search")],
        ),
        _view(
            "callsite",
            requires_query=True,
            capabilities=[_python("owner-callsite-search")],
        ),
        _view(
            "import",
            requires_query=True,
            capabilities=[_python("import-edge-search")],
        ),
        _view(
            "tests",
            requires_query=True,
            capabilities=[_python("pytest-test-owner-search")],
        ),
        _view(
            "lexical",
            requires_query=True,
            accepted_pipes=["owner", "tests"],
            supports_query_set=True,
            accepted_query_set_selectors=["lexical-set"],
            query_set_scopes=["project", "owner"],
            capabilities=[
                _semantic("lexical-candidate-search"),
                _python("parser-visible-source-lexical-search"),
            ],
            ingest_required_for=[
                _ingest("non-parser-text"),
                _ingest("docs-text"),
                _ingest("schema-json"),
                _ingest("generated-artifact"),
            ],
        ),
        _view(
            "reasoning",
            requires_query=True,
            capabilities=[
                _semantic("reasoning-owner-search"),
                _semantic("dependency-manifest-search"),
                _python("python-owner-item-query"),
                _python("pytest-test-owner-search"),
                _python("dependency-local-usage-search"),
            ],
        ),
        _view(
            "ingest",
            accepts_stdin=True,
            accepted_pipes=["items", "tests"],
            capabilities=[
                _semantic("external-candidate-ingest"),
                _semantic("stdin-shape-detection"),
                _semantic("owner-grouped-ingest"),
            ],
        ),
        _view(
            "semantic-facts",
            requires_query=True,
            accepts_stdin=True,
            capabilities=[
                _semantic("graph-turbo-provider-facts"),
                _python("python-ast-field-type-collection-facts"),
            ],
        ),
    ]
    from ._semantic_language_knowledge import python_knowledge_search_view_descriptors

    return (
        descriptors[:-2] + python_knowledge_search_view_descriptors() + descriptors[-2:]
    )


def _view(
    view: str,
    *,
    capabilities: Sequence[dict[str, str]],
    requires_query: bool = False,
    accepts_stdin: bool = False,
    accepted_pipes: Sequence[str] = (),
    supports_query_set: bool = False,
    accepted_query_set_selectors: Sequence[str] = (),
    query_set_scopes: Sequence[str] = (),
    fallbacks: Sequence[dict[str, object]] = (),
    ingest_required_for: Sequence[dict[str, str]] = (),
) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "method": f"search/{view}",
        "command": "search",
        "view": view,
        "requiresQuery": requires_query,
        "acceptsStdin": accepts_stdin,
        "supportsPackageScope": True,
        "capabilities": list(capabilities),
    }
    if accepted_pipes:
        descriptor["acceptedPipes"] = list(accepted_pipes)
    if supports_query_set:
        descriptor["supportsQuerySet"] = True
    if accepted_query_set_selectors:
        descriptor["acceptedQuerySetSelectors"] = list(accepted_query_set_selectors)
    if query_set_scopes:
        descriptor["querySetScopes"] = list(query_set_scopes)
    if fallbacks:
        descriptor["fallbacks"] = list(fallbacks)
    if ingest_required_for:
        descriptor["ingestRequiredFor"] = list(ingest_required_for)
    return descriptor


def _semantic(name: str) -> dict[str, str]:
    return _capability("semantic", name)


def _python(name: str) -> dict[str, str]:
    return _capability(_PYTHON_LANGUAGE_ID, name)


def _ingest(name: str) -> dict[str, str]:
    return _capability(_PYTHON_LANGUAGE_ID, name)


def _capability(namespace: str, name: str) -> dict[str, str]:
    return {"languageId": _PYTHON_LANGUAGE_ID, "namespace": namespace, "name": name}
