"""Hook query option helpers for the Python harness CLI."""

from __future__ import annotations

from ._semantic_selector_identity import python_structural_selector_owner_path


def normalize_query_surfaces(value: str | None) -> tuple[tuple[str, ...], str | None]:
    """Normalize shared hook query surfaces into py-harness search pipes."""
    if value is None:
        return (), "--surface requires owner,tests style surfaces"
    surfaces = tuple(surface.strip() for surface in value.split(",") if surface.strip())
    if not surfaces:
        return (), "--surface requires at least one surface"
    pipes: list[str] = []
    for surface in surfaces:
        pipe = "owner" if surface == "owners" else surface
        if pipe not in {"owner", "tests", "items"}:
            return (), f"unknown query surface: {surface}"
        pipes.append(pipe)
    return tuple(pipes), None


def normalize_query_view(value: str | None) -> tuple[str | None, str | None]:
    """Validate the shared hook query view flag."""
    if value == "metadata":
        return (
            None,
            "--view metadata is document-only for asp md/org query; "
            "Python query uses search --view seeds for discovery and "
            "query <owner-path> --term <symbol> --code or --names-only",
        )
    if value not in {"graph", "hits", "both", "seeds"}:
        return None, "--view requires graph, hits, both, or seeds"
    return value, None


def _selector_has_glob(selector: str) -> bool:
    return any(marker in selector for marker in ("*", "?", "[", "]", "{", "}"))


def owner_path_from_query_selector(selector: str | None) -> str | None:
    if selector is None:
        return None
    normalized = selector.replace("\\", "/").removeprefix("owner:")
    if any(marker in normalized for marker in ("*", "{", "}")):
        return None
    structural_owner_path = python_structural_selector_owner_path(selector)
    if structural_owner_path is not None:
        return structural_owner_path
    return None
