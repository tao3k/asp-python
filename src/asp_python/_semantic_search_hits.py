"""Public hit-builder facade for Python semantic search."""

from __future__ import annotations

from ._semantic_search_callsite_hits import callsite_hits
from ._semantic_search_import_test_hits import import_hits, test_path_hits
from ._semantic_search_symbol_hits import api_hits, symbol_hit, symbol_hits
from ._semantic_search_text_hits import text_hits

__all__ = [
    "api_hits",
    "callsite_hits",
    "import_hits",
    "symbol_hit",
    "symbol_hits",
    "test_path_hits",
    "text_hits",
]
