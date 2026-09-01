"""Import-context matching for Python public external type search."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ._semantic_search_deps import import_root, normalize_dependency_name
from ._semantic_search_public_external_type_model import (
    PublicExternalTypeImportContext,
    PublicExternalTypeSurface,
)

if TYPE_CHECKING:
    from python_lang_parser import PythonImport, PythonModuleReport


def dependency_import_contexts(
    module: PythonModuleReport,
    package: str,
) -> list[PublicExternalTypeImportContext]:
    """Return imports in a module that refer to the queried dependency."""

    return [
        context
        for import_record in module.imports
        for context in [_import_context(import_record, package)]
        if context is not None
    ]


def surface_import_context(
    surface: PublicExternalTypeSurface,
    contexts: list[PublicExternalTypeImportContext],
) -> tuple[PublicExternalTypeImportContext | None, bool]:
    """Return the matching import context and whether attribution is direct."""

    direct = next(
        (
            context
            for context in contexts
            if any(
                _contains_reference(surface.type_text, name)
                for name in context.direct_names
            )
        ),
        None,
    )
    if direct is not None:
        return direct, True
    possible = next(
        (
            context
            for context in contexts
            if any(
                _contains_reference(surface.type_text, name)
                for name in context.imported_names
            )
        ),
        None,
    )
    return (possible, False) if possible is not None else (None, False)


def _import_context(
    import_record: PythonImport,
    package: str,
) -> PublicExternalTypeImportContext | None:
    root = import_root(import_record.module, import_record.source_names)
    if root is None or normalize_dependency_name(root) != package:
        return None
    return PublicExternalTypeImportContext(
        dependency=package,
        import_specifier=import_record.module or root,
        direct_names=_direct_import_names(import_record, root),
        imported_names=tuple(
            name
            for name in (*import_record.names, *import_record.source_names)
            if name != "*"
        ),
    )


def _direct_import_names(import_record: PythonImport, root: str) -> tuple[str, ...]:
    names = [root]
    if import_record.module is None:
        names.extend(import_record.names)
    else:
        names.append(import_record.module)
    return tuple(dict.fromkeys(name for name in names if name and name != "*"))


def _contains_reference(text: str, name: str) -> bool:
    if not name:
        return False
    return bool(re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", text))
