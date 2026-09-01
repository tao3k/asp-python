"""Model objects for Python public external type search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PublicExternalTypeImportContext:
    dependency: str
    import_specifier: str
    direct_names: tuple[str, ...]
    imported_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PublicExternalTypeSurface:
    symbol: str
    api_kind: str
    surface: str
    type_text: str
    location: Any
