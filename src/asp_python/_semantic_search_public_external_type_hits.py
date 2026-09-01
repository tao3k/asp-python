"""Hit extraction for Python public external type search."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import dedupe_hits, location_from_source
from ._semantic_search_deps import module_owner_path
from ._semantic_search_public_external_type_imports import (
    dependency_import_contexts,
    surface_import_context,
)
from ._semantic_search_public_external_type_model import (
    PublicExternalTypeImportContext,
    PublicExternalTypeSurface,
)
from ._semantic_search_public_external_type_surfaces import public_type_surfaces

if TYPE_CHECKING:
    from python_lang_parser import PythonModuleReport

    from ._model import AspPythonReport


def public_external_type_hits(
    report: AspPythonReport,
    project_root: Path,
    package: str,
) -> list[dict[str, Any]]:
    """Return public API surfaces that expose a dependency type."""

    hits = [
        hit
        for module in report.modules
        for hit in _module_public_external_type_hits(module, project_root, package)
    ]
    return dedupe_hits(hits)


def _module_public_external_type_hits(
    module: PythonModuleReport,
    project_root: Path,
    package: str,
) -> list[dict[str, Any]]:
    contexts = dependency_import_contexts(module, package)
    if not contexts:
        return []
    owner_path = module_owner_path(module, project_root)
    return [
        _surface_hit(surface, owner_path, project_root, context, direct=direct)
        for surface in public_type_surfaces(module)
        for context, direct in [surface_import_context(surface, contexts)]
        if context is not None
    ]


def _surface_hit(
    surface: PublicExternalTypeSurface,
    owner_path: str,
    project_root: Path,
    context: PublicExternalTypeImportContext,
    *,
    direct: bool,
) -> dict[str, Any]:
    return {
        "kind": "api",
        "ownerPath": owner_path,
        "location": location_from_source(surface.location, project_root),
        "score": 9 if direct else 4,
        "reason": "public-external-type" if direct else "possible-public-external-type",
        "symbol": surface.symbol,
        "fields": {
            "source": "native-parser",
            "dependency": context.dependency,
            "confidence": "direct" if direct else "possible",
            "apiKind": surface.api_kind,
            "surface": surface.surface,
            "typeText": surface.type_text,
            "importSpecifier": context.import_specifier,
        },
    }
