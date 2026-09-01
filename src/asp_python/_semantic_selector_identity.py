"""Canonical parser-owned selector identity helpers."""

from __future__ import annotations


def python_structural_selector_identity(
    selector: str | None,
) -> tuple[str, str, str] | None:
    """Return the canonical owner, kind, and name for a Python item selector."""

    if selector is None:
        return None
    normalized = selector.replace("\\", "/").removeprefix("owner:")
    if any(marker in normalized for marker in ("*", "{", "}")):
        return None
    if not normalized.startswith("python://"):
        return None
    owner_path, marker, item_identity = normalized.removeprefix("python://").partition(
        "#item/"
    )
    kind, separator, name = item_identity.partition("/")
    if not marker or not owner_path or not separator or not kind or not name:
        return None
    return (owner_path, kind, name)


def python_structural_selector_owner_path(selector: str | None) -> str | None:
    """Return the canonical owner path when *selector* is structural."""

    identity = python_structural_selector_identity(selector)
    return identity[0] if identity is not None else None
