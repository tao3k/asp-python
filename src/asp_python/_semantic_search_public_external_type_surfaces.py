"""Public Python API surface extraction for external type search."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._semantic_search_public_external_type_model import PublicExternalTypeSurface

if TYPE_CHECKING:
    from python_lang_parser import (
        PythonAssignmentTarget,
        PythonModuleReport,
        PythonSymbol,
    )


def public_type_surfaces(module: PythonModuleReport) -> list[PublicExternalTypeSurface]:
    """Return parser-owned public type surfaces for one module."""

    surfaces: list[PublicExternalTypeSurface] = []
    for symbol in module.symbols:
        if symbol.is_public and symbol.is_top_level:
            surfaces.extend(_symbol_type_surfaces(module, symbol))
    for assignment in module.assignments:
        if assignment.is_public and assignment.is_top_level:
            surface = _assignment_type_surface(module, assignment)
            if surface is not None:
                surfaces.append(surface)
    return surfaces


def _symbol_type_surfaces(
    module: PythonModuleReport,
    symbol: PythonSymbol,
) -> list[PublicExternalTypeSurface]:
    surfaces: list[PublicExternalTypeSurface] = []
    header_text = _symbol_header_text(module, symbol)
    if header_text:
        surfaces.append(
            PublicExternalTypeSurface(
                symbol=symbol.qualified_name,
                api_kind=symbol.kind.value,
                surface="signature",
                type_text=header_text,
                location=symbol.location,
            )
        )
    surfaces.extend(
        PublicExternalTypeSurface(
            symbol=symbol.qualified_name,
            api_kind=symbol.kind.value,
            surface="decorator",
            type_text=decorator,
            location=symbol.location,
        )
        for decorator in symbol.decorators
    )
    surfaces.extend(
        PublicExternalTypeSurface(
            symbol=symbol.qualified_name,
            api_kind=symbol.kind.value,
            surface="base",
            type_text=base_class,
            location=symbol.location,
        )
        for base_class in symbol.base_classes
    )
    return surfaces


def _assignment_type_surface(
    module: PythonModuleReport,
    assignment: PythonAssignmentTarget,
) -> PublicExternalTypeSurface | None:
    source_line = module.source_line(assignment.location.line)
    if source_line is None or ":" not in source_line:
        return None
    return PublicExternalTypeSurface(
        symbol=assignment.name,
        api_kind="assignment",
        surface="annotation",
        type_text=source_line.strip()[:200],
        location=assignment.location,
    )


def _symbol_header_text(module: PythonModuleReport, symbol: PythonSymbol) -> str:
    start = max(1, symbol.location.line)
    end = min(symbol.end_line or start, start + 8)
    lines = module.source_lines[start - 1 : end]
    if not lines:
        return ""
    balance = 0
    selected: list[str] = []
    for line in lines:
        stripped = line.strip()
        selected.append(stripped)
        balance += stripped.count("(") + stripped.count("[") + stripped.count("{")
        balance -= stripped.count(")") + stripped.count("]") + stripped.count("}")
        if stripped.endswith(":") and balance <= 0:
            break
        if len(selected) >= 8:
            break
    return " ".join(selected)[:240]
