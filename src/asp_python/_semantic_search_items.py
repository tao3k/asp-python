"""Parser-owned compact item extraction for Python owner searches."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import _semantic_language_ids as ids
from ._python_compact import compact_python_item
from ._semantic_query_packet import (
    semantic_import_route_next,
    semantic_query_coverage,
    semantic_query_match,
    semantic_query_match_mode,
)
from ._semantic_search_common import compact_fields, semantic_search_display_path
from ._semantic_search_import_routes import import_definition_routes
from ._semantic_search_model import MAX_OWNER_QUERY_ITEMS
from ._semantic_selector_identity import python_structural_selector_identity

if TYPE_CHECKING:
    from python_lang_parser import PythonModuleReport, PythonSymbol

    from ._model import AspPythonReport


def owner_item_query_payload(
    report: AspPythonReport,
    project_root: Path,
    owner_path: str,
    item_query: str | None,
) -> dict[str, Any]:
    """Return compact parser item facts for one owner path."""

    module = _module_for_owner(report, project_root, owner_path)
    if module is None:
        return {
            "items": [],
            "fields": {"item": 0, "itemStatus": "miss", "itemMatch": "none"},
            "notes": [{"kind": "owner-not-found", "message": owner_path}],
        }

    symbols = _sorted_symbols(module)
    terms = _query_terms(item_query)
    selected, match = _select_symbols(module, symbols, terms)
    import_routes = (
        import_definition_routes(report, project_root, module, terms)
        if terms and match != "exact"
        else []
    )
    fallback = False
    if import_routes:
        selected = []
        match = "candidate"
    elif not selected:
        selected = [symbol for symbol in symbols if symbol.is_top_level][
            :MAX_OWNER_QUERY_ITEMS
        ]
        match = "none" if terms else "top-items"
        fallback = bool(terms)

    items = [
        _item_record(module, project_root, owner_path, symbol)
        for symbol in selected[:MAX_OWNER_QUERY_ITEMS]
    ]
    fields: dict[str, object] = {
        "item": len(items),
        "itemQuery": item_query,
        "itemStatus": "hit" if items and not fallback else "miss",
        "itemMatch": match if items or import_routes else "none",
        "fallback": "owner-top-items" if fallback and items else None,
        "next": semantic_import_route_next(import_routes[0]) if import_routes else None,
    }
    return {
        "items": items,
        "fields": compact_fields(fields),
        "notes": _item_query_notes(item_query, owner_path, items, import_routes),
        "importRoutes": import_routes,
    }


def owner_item_semantic_query_packet(
    report: AspPythonReport,
    project_root: Path,
    owner_path: str,
    item_query: str,
    *,
    output_mode: str,
    selector: str | None = None,
) -> dict[str, Any]:
    """Return a semantic-query-packet for owner-local Python item lookup."""

    payload = owner_item_query_payload(report, project_root, owner_path, item_query)
    items, fields, import_routes = _selector_resolved_owner_items(
        report,
        project_root,
        owner_path,
        selector,
        payload,
    )
    return _owner_item_semantic_query_packet(
        payload,
        project_root,
        owner_path,
        item_query,
        output_mode,
        items,
        fields,
        import_routes,
    )


def _selector_resolved_owner_items(
    report: AspPythonReport,
    project_root: Path,
    owner_path: str,
    selector: str | None,
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[Any]]:
    items = payload["items"]
    fields = payload["fields"]
    import_routes = payload.get("importRoutes", [])
    module = _module_for_owner(report, project_root, owner_path)
    selector_identity = python_structural_selector_identity(selector)
    if selector_identity is not None:
        selector_owner_path, selector_kind, selector_name = selector_identity
        items = (
            [
                _item_record(module, project_root, owner_path, symbol)
                for symbol in _sorted_symbols(module)
                if symbol.kind.value == selector_kind
                and symbol.qualified_name == selector_name
            ]
            if selector_owner_path == owner_path and module is not None
            else []
        )
        fields = {
            **fields,
            "item": len(items),
            "itemStatus": "hit" if items else "miss",
            "itemMatch": "exact" if items else "none",
        }
        import_routes = []
    return items, fields, import_routes


def _owner_item_semantic_query_packet(
    payload: dict[str, Any],
    project_root: Path,
    owner_path: str,
    item_query: str,
    output_mode: str,
    items: list[dict[str, Any]],
    fields: dict[str, Any],
    import_routes: list[Any],
) -> dict[str, Any]:
    terms = _query_terms(item_query)
    from ._semantic_syntax_refs import (
        annotate_python_owner_item_syntax_refs,
        attach_python_syntax_refs,
    )

    syntax_refs = annotate_python_owner_item_syntax_refs(items)
    packet = {
        "schemaId": ids.SEMANTIC_QUERY_PACKET_SCHEMA_ID,
        "schemaVersion": "1",
        "protocolId": ids.SEMANTIC_LANGUAGE_PROTOCOL_ID,
        "protocolVersion": ids.SEMANTIC_LANGUAGE_PROTOCOL_VERSION,
        "languageId": ids.PYTHON_LANGUAGE_ID,
        "providerId": ids.PYTHON_PROVIDER_ID,
        "binary": ids.PYTHON_BINARY,
        "namespace": ids.PYTHON_PROVIDER_NAMESPACE,
        "method": "query/owner-items",
        "projectRoot": str(project_root),
        "ownerPath": owner_path,
        "query": item_query,
        "queryTerms": terms,
        "matchMode": semantic_query_match_mode(str(fields.get("itemMatch", "none"))),
        "outputMode": output_mode,
        "patchSafety": {
            "level": "read-safe",
            "reason": "compact query packet is not a mutation authority",
            "nextAction": (
                "query --selector <structural-selector> --projection source"
            ),
        },
        "queryCoverage": [
            semantic_query_coverage(
                term,
                items,
                str(fields.get("itemMatch", "none")),
                import_routes if isinstance(import_routes, list) else [],
            )
            for term in terms
        ],
        "matches": [
            semantic_query_match(item, include_code=output_mode != "names")
            for item in items
        ],
        "truncated": any(
            bool(item.get("fields", {}).get("truncated")) for item in items
        ),
        "notes": payload.get("notes", []),
    }
    attach_python_syntax_refs(packet, syntax_refs)
    return packet


def _module_for_owner(
    report: AspPythonReport,
    project_root: Path,
    owner_path: str,
) -> PythonModuleReport | None:
    for module in report.modules:
        if (
            module.path is not None
            and semantic_search_display_path(module.path, project_root) == owner_path
        ):
            return module
    return None


def _sorted_symbols(module: PythonModuleReport) -> list[PythonSymbol]:
    return sorted(
        module.symbols,
        key=lambda symbol: (
            symbol.location.line,
            symbol.location.column,
            symbol.qualified_name,
        ),
    )


def _query_terms(item_query: str | None) -> list[str]:
    if item_query is None:
        return []
    return [term.strip() for term in item_query.split("|") if term.strip()]


def _item_query_notes(
    item_query: str | None,
    owner_path: str,
    items: list[dict[str, Any]],
    import_routes: list[dict[str, str]],
) -> list[dict[str, str]]:
    if import_routes:
        route = import_routes[0]
        return [
            {
                "kind": "imported-definition",
                "message": (
                    f"{item_query or owner_path} is imported in {owner_path}; "
                    f"next={semantic_import_route_next(route)}"
                ),
            }
        ]
    if items:
        return []
    return [{"kind": "item-not-found", "message": item_query or owner_path}]


def _select_symbols(
    module: PythonModuleReport,
    symbols: list[PythonSymbol],
    terms: list[str],
) -> tuple[list[PythonSymbol], str]:
    if not terms:
        return [symbol for symbol in symbols if symbol.is_top_level], "top-items"
    exact = _dedupe_symbols(
        symbol
        for term in terms
        for symbol in symbols
        if term in {symbol.name, symbol.qualified_name}
    )
    if exact:
        return exact, "exact"
    folded_terms = [term.casefold() for term in terms]
    contains = _dedupe_symbols(
        symbol
        for term in folded_terms
        for symbol in symbols
        if term in _symbol_query_text(module, symbol)
    )
    return contains, "fallback-contains" if contains else "none"


def _symbol_query_text(module: PythonModuleReport, symbol: PythonSymbol) -> str:
    end_line = symbol.end_line or symbol.location.line
    code, _, _ = _compact_code(
        module,
        str(symbol.location.path or ""),
        symbol.location.line,
        end_line,
    )
    return "\n".join((symbol.name, symbol.qualified_name, code)).casefold()


def _dedupe_symbols(symbols: Iterable[PythonSymbol]) -> list[PythonSymbol]:
    selected: list[PythonSymbol] = []
    seen: set[tuple[str, int, int]] = set()
    for symbol in symbols:
        key = (symbol.qualified_name, symbol.location.line, symbol.location.column)
        if key in seen:
            continue
        seen.add(key)
        selected.append(symbol)
    return selected


def _item_record(
    module: PythonModuleReport,
    project_root: Path,
    owner_path: str,
    symbol: PythonSymbol,
) -> dict[str, Any]:
    end_line = symbol.end_line or symbol.location.line
    line_range = f"{symbol.location.line}:{end_line}"
    source_locator_hint = f"{owner_path}:{symbol.location.line}:{end_line}"
    structural_selector = _structural_selector(owner_path, symbol)
    code, truncated, projection_nodes = _compact_code(
        module,
        owner_path,
        symbol.location.line,
        end_line,
    )
    return {
        "name": symbol.qualified_name,
        "kind": symbol.kind.value,
        "ownerPath": owner_path,
        "location": {
            "path": owner_path,
            "lineRange": line_range,
        },
        "fields": compact_fields(
            {
                "public": symbol.is_public,
                "doc": bool(symbol.docstring),
                "structuralSelector": structural_selector,
                "displayLineRange": line_range,
                "sourceLocatorHint": source_locator_hint,
                "read": source_locator_hint,
                "reason": "item-query",
                "truncated": truncated,
                "code": code,
                "projectionNodes": projection_nodes,
                "sourcePath": semantic_search_display_path(
                    symbol.location.path or owner_path, project_root
                ),
            }
        ),
    }


def _structural_selector(owner_path: str, symbol: PythonSymbol) -> str:
    return f"python://{owner_path}#item/{symbol.kind.value}/{symbol.qualified_name}"


def _compact_code(
    module: PythonModuleReport,
    owner_path: str,
    start_line: int,
    end_line: int,
    *,
    max_lines: int = 80,
) -> tuple[str, bool, list[dict[str, Any]]]:
    raw_lines = module.source_lines[start_line - 1 : end_line]
    compact = compact_python_item(raw_lines, owner_path, start_line)
    if compact.projection_nodes:
        return compact.code, False, compact.projection_nodes

    truncated = len(raw_lines) > max_lines
    selected_lines = raw_lines[:max_lines]
    compact = compact_python_item(selected_lines, owner_path, start_line)
    return compact.code, truncated, compact.projection_nodes
