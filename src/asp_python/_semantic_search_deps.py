"""Dependency-specific Python semantic-search facts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._semantic_search_common import location_from_source
from ._semantic_search_model import Fields

if TYPE_CHECKING:
    from collections.abc import Sequence

    from python_lang_parser import PythonProjectDependency

    from ._model import AspPythonReport


def dependency_node(
    dependency: PythonProjectDependency,
    *,
    parts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return one dependency node for a search packet."""

    fields: Fields = {
        "requirement": dependency.requirement,
        "source": dependency.source,
        "versionScope": version_scope(parts or {}, [dependency]),
    }
    if dependency.group:
        fields["group"] = dependency.group
    if dependency.extra:
        fields["extra"] = dependency.extra
    if parts is not None and parts.get("requestedVersion"):
        fields["requestedVersion"] = parts["requestedVersion"]
    if parts is not None and parts.get("apiQuery"):
        fields["apiQuery"] = parts["apiQuery"]
    return {"id": f"D:{dependency.name}", "kind": "dependency", "fields": fields}


def dependency_query_parts(query: str) -> dict[str, str]:
    """Parse `<package[@version][::api]>` into compact fields."""

    package_part, _, api_query = query.partition("::")
    package_name = package_part
    requested_version = ""
    if "@" in package_part and not package_part.startswith("@"):
        package_name, requested_version = package_part.rsplit("@", 1)
    elif "==" in package_part:
        package_name, requested_version = package_part.split("==", 1)
    return {
        "package": normalize_dependency_name(package_name.strip()),
        "requestedVersion": requested_version.strip(),
        "apiQuery": api_query.strip(),
    }


def normalize_dependency_name(value: str) -> str:
    """Normalize Python dependency names for query matching."""

    return re.sub(r"[-_.]+", "-", value).casefold()


def dependency_matches(dependency: PythonProjectDependency, query: str) -> bool:
    """Return whether a metadata dependency matches a normalized query."""

    return query in {
        normalize_dependency_name(dependency.name),
        normalize_dependency_name(dependency.requirement.split()[0]),
    }


def version_scope(
    parts: dict[str, str],
    matches: Sequence[PythonProjectDependency],
) -> str:
    """Return the current/external/unknown version scope label."""

    if not matches:
        return "external" if parts.get("requestedVersion") else "unknown"
    requested = parts.get("requestedVersion", "")
    if not requested:
        return "current"
    return (
        "current"
        if any(requested in item.requirement for item in matches)
        else "external"
    )


def dependency_usage_hits(
    report: AspPythonReport,
    project_root: Path,
    package_query: str,
) -> list[dict[str, Any]]:
    """Return local import usage hits for a dependency name."""

    hits: list[dict[str, Any]] = []
    for module in report.modules:
        owner_path = module_owner_path(module, project_root)
        for import_record in module.imports:
            root_name = import_root(import_record.module, import_record.names)
            if root_name is None:
                continue
            if normalize_dependency_name(root_name) != package_query:
                continue
            hits.append(
                {
                    "kind": "dependency",
                    "ownerPath": owner_path,
                    "location": location_from_source(
                        import_record.location, project_root
                    ),
                    "score": 3,
                    "reason": "import-usage",
                    "symbol": root_name,
                    "fields": {"scope": import_record.scope or "module"},
                }
            )
    return hits


def module_owner_path(module, project_root: Path) -> str:
    """Return a display path for a parsed module."""

    from ._semantic_search_common import semantic_search_display_path

    return semantic_search_display_path(module.path or ".", project_root)


def import_root(module: str | None, names) -> str | None:
    """Return the root package named by a Python import statement."""

    if module:
        return module.split(".", 1)[0]
    if names:
        return names[0].split(".", 1)[0]
    return None
