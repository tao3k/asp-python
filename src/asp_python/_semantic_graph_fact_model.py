"""Shared model for Python graph-turbo provider facts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

COLLECTION_NAMES = {
    "list": "list",
    "List": "list",
    "Sequence": "list",
    "MutableSequence": "list",
    "tuple": "tuple",
    "Tuple": "tuple",
    "set": "set",
    "Set": "set",
    "frozenset": "set",
    "dict": "dict",
    "Dict": "dict",
    "Mapping": "dict",
    "MutableMapping": "dict",
}


@dataclass(frozen=True, slots=True)
class FieldFact:
    path: str
    container_name: str
    field_name: str
    type_value: str
    collection_kind: str | None
    line: int
    context_start: int
    context_end: int


@dataclass(frozen=True, slots=True)
class PackageFact:
    name: str
    manifest_path: str


@dataclass(frozen=True, slots=True)
class DependencyFact:
    package_name: str
    dependency_name: str
    dependency_kind: str
    manifest_path: str
    version_req: str | None = None
    extra: str | None = None


@dataclass(frozen=True, slots=True)
class TestFact:
    path: str
    name: str
    function_count: int


@dataclass(frozen=True, slots=True)
class ProjectFact:
    package: PackageFact
    dependencies: tuple[DependencyFact, ...]
    tests: tuple[TestFact, ...]


def display_path(project_root: Path, path: Path) -> str:
    return path.relative_to(project_root).as_posix()


def collection_kind(type_value: str) -> str | None:
    root = type_value.split("[", 1)[0].split(".", 1)[-1]
    return COLLECTION_NAMES.get(root)
