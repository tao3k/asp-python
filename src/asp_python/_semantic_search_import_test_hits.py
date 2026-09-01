"""Import and test hit builders for Python semantic search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import location_from_source, path_hit
from ._semantic_search_deps import module_owner_path
from .verification.facts import is_test_path

if TYPE_CHECKING:
    from ._model import AspPythonReport


def import_hits(
    report: AspPythonReport,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    """Return raw import-statement hits."""

    query_folded = query.casefold()
    return [
        _import_hit(
            import_record, module_owner_path(module, project_root), project_root
        )
        for module in report.modules
        for import_record in module.imports
        if _import_matches(import_record, query_folded)
    ]


def test_path_hits(
    report: AspPythonReport,
    project_root: Path,
    query: str,
) -> list[dict[str, Any]]:
    """Return test path/function hits."""

    query_folded = query.casefold()
    return [
        path_hit(owner_path, owner_path, kind="test", score=3, reason="test-path")
        for module in report.modules
        if is_test_path(owner_path := module_owner_path(module, project_root))
        if _test_module_matches(module, owner_path, query_folded)
    ]


def _import_hit(import_record, owner_path: str, project_root: Path) -> dict[str, Any]:
    return {
        "kind": "import",
        "ownerPath": owner_path,
        "location": location_from_source(import_record.location, project_root),
        "score": 3,
        "reason": "import-statement",
        "symbol": import_record.module or ",".join(import_record.names),
        "fields": {"scope": import_record.scope or "module"},
    }


def _import_matches(import_record, query_folded: str) -> bool:
    haystacks = [
        import_record.module or "",
        *import_record.names,
        *import_record.source_names,
    ]
    return any(query_folded in item.casefold() for item in haystacks)


def _test_module_matches(module, owner_path: str, query_folded: str) -> bool:
    if query_folded in owner_path.casefold():
        return True
    return any(query_folded in symbol.name.casefold() for symbol in module.symbols)
