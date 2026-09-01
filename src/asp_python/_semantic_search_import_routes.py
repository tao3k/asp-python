"""Import-definition route candidates for Python owner item queries."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import semantic_search_display_path

if TYPE_CHECKING:
    from python_lang_parser import PythonModuleReport

    from ._project_policy_context import AspPythonReport


def import_definition_routes(
    report: AspPythonReport,
    project_root: Path,
    module: PythonModuleReport,
    terms: list[str],
) -> list[dict[str, str]]:
    owner_paths = tuple(_report_owner_paths(report, project_root))
    routes: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for term in terms:
        routes.extend(_routes_for_term(term, module.imports, owner_paths, seen))
    return routes


def _routes_for_term(
    term: str,
    imports: object,
    owner_paths: tuple[str, ...],
    seen: set[tuple[str, str, str]],
) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    for imported in imports:
        route = _route_for_import(term, imported, owner_paths)
        if route is None:
            continue
        key = (route["term"], route["ownerPath"], route["query"])
        if key in seen:
            continue
        seen.add(key)
        routes.append(route)
    return routes


def _route_for_import(
    term: str,
    imported: Any,
    owner_paths: tuple[str, ...],
) -> dict[str, str] | None:
    source_name = _import_source_name_for_term(imported, term)
    if source_name is None:
        return None
    owner_path = _import_target_owner(owner_paths, imported)
    if owner_path is None:
        return None
    return {"term": term, "ownerPath": owner_path, "query": source_name}


def _report_owner_paths(
    report: AspPythonReport,
    project_root: Path,
) -> list[str]:
    owner_paths: list[str] = []
    for report_module in report.modules:
        path = report_module.path
        if path is None:
            continue
        owner_paths.append(semantic_search_display_path(path, project_root))
    return owner_paths


def _import_source_name_for_term(imported: Any, term: str) -> str | None:
    names = tuple(str(name) for name in getattr(imported, "names", ()))
    source_names = tuple(str(name) for name in getattr(imported, "source_names", ()))
    if term in names:
        index = names.index(term)
        if index < len(source_names) and source_names[index] != "*":
            return source_names[index]
        return term
    if term in source_names and term != "*":
        return term
    return None


def _import_target_owner(owner_paths: tuple[str, ...], imported: Any) -> str | None:
    module_name = getattr(imported, "module", None)
    if not isinstance(module_name, str) or not module_name:
        return None
    candidates = _module_owner_suffixes(module_name)
    return next(
        (owner_path for owner_path in owner_paths if owner_path.endswith(candidates)),
        None,
    )


def _module_owner_suffixes(module_name: str) -> tuple[str, str]:
    module_suffix = module_name.replace(".", "/")
    return (f"{module_suffix}.py", f"{module_suffix}/__init__.py")
