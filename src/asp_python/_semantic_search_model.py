"""Shared semantic-search model aliases for the Python provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FieldValue = str | int | float | bool | list[str | int | float | bool]
Fields = dict[str, FieldValue]

MAX_PRIME_OWNERS = 8
MAX_PRIME_EDGES = 24
MAX_WORKSPACE_PACKAGES = 24
MAX_WORKSPACE_EDGES = 8
MAX_FINDINGS = 8
MAX_LEXICAL_HITS = 12
MAX_SYMBOL_HITS = 20
MAX_IMPORT_HITS = 30
MAX_DEPENDENCY_HITS = 24
MAX_TEST_HITS = 8
MAX_OWNER_QUERY_ITEMS = 4


@dataclass(frozen=True, slots=True)
class PythonSemanticSearchOptions:
    """Options parsed from an `asp-python search` invocation."""

    view: str
    query: str | None = None
    item_query: str | None = None
    query_set: tuple[str, ...] = ()
    owner_path: str | None = None
    dependency: str | None = None
    pipes: tuple[str, ...] = ()
    render_mode: str | None = None
    stdin: str = ""
    runtime_cost: dict[str, Any] | None = None
