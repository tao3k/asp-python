"""Public API surfaces that expose external dependency types."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import (
    header,
)
from ._semantic_search_deps import (
    dependency_matches,
    normalize_dependency_name,
)
from ._semantic_search_model import MAX_SYMBOL_HITS
from ._semantic_search_owners import owners_for_paths
from ._semantic_search_packages import dependencies
from ._semantic_search_public_external_type_hits import public_external_type_hits
from ._semantic_search_view_hits import hit_next_actions

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonReasoningTreeFacts,
    )

    from ._model import AspPythonReport


def public_external_types_payload(
    report: AspPythonReport,
    facts: PythonReasoningTreeFacts,
    project_root: Path,
    query: str,
) -> dict[str, Any]:
    """Build public external type/API payloads."""

    package = normalize_dependency_name(query.strip())
    manifest_matches = _manifest_matches(facts, package)
    hits = (
        []
        if not package
        else public_external_type_hits(report, project_root, package)[:MAX_SYMBOL_HITS]
    )
    type_surfaces = _public_external_type_surfaces(hits, package)
    owners = owners_for_paths(facts, project_root, [hit["ownerPath"] for hit in hits])
    confirmed = sum(1 for hit in hits if hit["reason"] == "public-external-type")
    possible = sum(
        1 for hit in hits if hit["reason"] == "possible-public-external-type"
    )
    return {
        "header": header(
            "public-external-types",
            {
                "q": query,
                "package": package,
                "manifest": len(manifest_matches),
                "own": len(owners),
                "hit": len(hits),
                "source": "native-parser",
                "view": "hits",
            },
        ),
        "nodes": [
            {
                "id": f"D:{package}",
                "kind": "dependency",
                "fields": {
                    "manifest": len(manifest_matches),
                    "confirmed": confirmed,
                    "possible": possible,
                },
            }
        ]
        if package
        else [],
        "owners": owners,
        "hits": hits,
        "typeSurfaces": type_surfaces,
        "nextActions": (
            ([] if not package else [{"kind": "dependency", "target": package}])
            + hit_next_actions(hits)
        )[:8],
        "notes": _public_external_type_notes(query, hits),
    }


def _manifest_matches(facts: PythonReasoningTreeFacts, package: str):
    return [item for item in dependencies(facts) if dependency_matches(item, package)]


def _public_external_type_surfaces(
    hits: list[dict[str, Any]],
    package: str,
) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for index, hit in enumerate(hits):
        surface_doc = _public_external_type_surface(hit, package, index)
        if surface_doc is None:
            continue
        surfaces.append(surface_doc)
    return surfaces


def _public_external_type_surface(
    hit: dict[str, Any],
    package: str,
    index: int,
) -> dict[str, Any] | None:
    parts = _public_external_type_hit_parts(hit, package)
    if parts is None:
        return None
    surface_doc = _public_external_type_surface_doc(
        parts["owner_path"],
        parts["name"],
        parts["type_text"],
        parts["surface"],
        parts["api_kind"],
        package,
        parts["import_specifier"],
        parts["fields"],
        index,
    )
    _attach_public_external_type_location(surface_doc, hit)
    return surface_doc


def _public_external_type_hit_parts(
    hit: dict[str, Any],
    package: str,
) -> dict[str, Any] | None:
    fields = hit.get("fields", {})
    if not isinstance(fields, dict):
        return None
    owner_path = _string_field(hit.get("ownerPath"))
    if owner_path is None:
        return None
    symbol = _string_field(hit.get("symbol"))
    surface = _string_field(fields.get("surface"))
    api_kind = _string_field(fields.get("apiKind"))
    type_text = _string_field(fields.get("typeText")) or symbol or "unknown"
    import_specifier = _string_field(fields.get("importSpecifier")) or package
    name = symbol or type_text
    return {
        "fields": fields,
        "owner_path": owner_path,
        "name": name,
        "type_text": type_text,
        "surface": surface,
        "api_kind": api_kind,
        "import_specifier": import_specifier,
    }


def _attach_public_external_type_location(
    surface_doc: dict[str, Any],
    hit: dict[str, Any],
) -> None:
    location = hit.get("location")
    if isinstance(location, dict):
        surface_doc["location"] = location


def _public_external_type_surface_doc(
    owner_path: str,
    name: str,
    type_text: str,
    surface: str | None,
    api_kind: str | None,
    package: str,
    import_specifier: str,
    fields: dict[Any, Any],
    index: int,
) -> dict[str, Any]:
    return {
        "id": f"PY:{owner_path}:{name}:{surface or index}",
        "name": name,
        "languageName": name,
        "qualifiedName": type_text,
        "kind": _type_surface_kind(api_kind, surface),
        "role": _type_surface_role(api_kind, surface),
        "ownerPath": owner_path,
        "visibility": "public",
        "external": True,
        "source": _string_field(fields.get("source")) or "native-parser",
        "package": package,
        "module": import_specifier,
        "symbol": name,
        "carrier": _public_external_type_carrier(
            type_text,
            api_kind,
            package,
            import_specifier,
        ),
        "fields": _type_surface_fields(fields, package),
    }


def _public_external_type_carrier(
    type_text: str,
    api_kind: str | None,
    package: str,
    import_specifier: str,
) -> dict[str, Any]:
    return {
        "name": type_text,
        "languageName": type_text,
        "qualifiedName": type_text,
        "carrier": _carrier_kind(type_text, api_kind),
        "package": package,
        "module": import_specifier,
        "versionScope": "external",
        "external": True,
    }


def _type_surface_fields(
    fields: dict[Any, Any],
    package: str,
) -> dict[str, Any]:
    surface_fields: dict[str, Any] = {"dependency": package}
    for key, value in fields.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, (str, int, float, bool)):
            surface_fields[key] = value
        elif isinstance(value, list) and all(
            isinstance(item, (str, int, float, bool)) for item in value
        ):
            surface_fields[key] = value
    return surface_fields


def _string_field(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _type_surface_kind(api_kind: str | None, surface: str | None) -> str:
    if api_kind == "class":
        return "class"
    if api_kind == "function":
        return "function"
    if api_kind == "type":
        return "alias"
    if surface and surface.startswith("field:"):
        return "object"
    return "unknown"


def _type_surface_role(api_kind: str | None, surface: str | None) -> str:
    if surface and surface.startswith("param:"):
        return "api-input"
    if surface in {"return", "success"}:
        return "api-output"
    if surface == "error":
        return "api-error"
    if surface and surface.startswith("field:"):
        return "api-field"
    if surface == "alias" or api_kind == "type":
        return "public-type-alias"
    return "external-dependency"


def _carrier_kind(type_text: str, api_kind: str | None) -> str:
    stripped = type_text.strip()
    lowered = stripped.lower()
    if "|" in stripped or lowered.startswith("typing.union["):
        return "union"
    if lowered.startswith(("list[", "tuple[", "set[", "frozenset[", "sequence[")):
        return "array"
    if lowered.startswith(("dict[", "mapping[", "mutablemapping[")):
        return "map"
    if api_kind == "class" or lowered.startswith("class "):
        return "class"
    if api_kind == "function" or lowered.startswith("def "):
        return "function"
    if stripped in {"str", "int", "float", "bool", "bytes", "None"}:
        return "primitive"
    return "external"


def _public_external_type_notes(
    query: str,
    hits: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if not query.strip():
        return [
            {
                "kind": "empty-query",
                "message": "public-external-types search requires a dependency package query",
            }
        ]
    if not hits:
        return [
            {
                "kind": "not-found",
                "message": f"public external type surfaces not found: {query}",
            }
        ]
    return []
