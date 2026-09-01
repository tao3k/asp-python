"""Collect Python package/build/test graph facts from project metadata."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ._project_config import read_pyproject_payload
from ._semantic_graph_fact_collect import SKIP_DIRS
from ._semantic_graph_fact_model import (
    DependencyFact,
    PackageFact,
    ProjectFact,
    TestFact,
    display_path,
)

DEPENDENCY_LIMIT = 64
TEST_LIMIT = 64
PYTHON_SUFFIX = ".py"


def collect_project_facts(project_root: Path) -> ProjectFact | None:
    manifest_path = project_root / "pyproject.toml"
    pyproject = _read_pyproject(manifest_path)
    project = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
    if not isinstance(project, dict):
        return None
    package_name = project.get("name")
    if not isinstance(package_name, str) or not package_name.strip():
        return None
    package = PackageFact(
        name=package_name.strip(),
        manifest_path=display_path(project_root, manifest_path),
    )
    return ProjectFact(
        package=package,
        dependencies=tuple(_dependency_facts(project, package.manifest_path)),
        tests=tuple(_test_facts(project_root)),
    )


def _read_pyproject(path: Path) -> dict[str, Any]:
    return read_pyproject_payload(path)


def _dependency_facts(
    project: dict[str, Any],
    manifest_path: str,
) -> list[DependencyFact]:
    facts: list[DependencyFact] = []
    dependencies = project.get("dependencies", [])
    if isinstance(dependencies, list):
        facts.extend(
            fact
            for dependency in dependencies
            if isinstance(dependency, str)
            if (fact := _dependency_fact(dependency, "normal", manifest_path))
            is not None
        )
    optional = project.get("optional-dependencies", {})
    if isinstance(optional, dict):
        for extra, dependencies in sorted(optional.items()):
            if not isinstance(extra, str) or not isinstance(dependencies, list):
                continue
            dependency_kind = "dev" if extra in {"dev", "test", "tests"} else "optional"
            facts.extend(
                fact
                for dependency in dependencies
                if isinstance(dependency, str)
                if (
                    fact := _dependency_fact(
                        dependency,
                        dependency_kind,
                        manifest_path,
                        extra=extra,
                    )
                )
                is not None
            )
    return sorted(facts, key=lambda fact: (fact.dependency_kind, fact.dependency_name))[
        :DEPENDENCY_LIMIT
    ]


def _dependency_fact(
    requirement: str,
    dependency_kind: str,
    manifest_path: str,
    *,
    extra: str | None = None,
) -> DependencyFact | None:
    dependency_name = _dependency_name(requirement)
    if dependency_name is None:
        return None
    version_req = requirement[len(dependency_name) :].strip()
    return DependencyFact(
        package_name=dependency_name.replace("_", "-"),
        dependency_name=dependency_name,
        dependency_kind=dependency_kind,
        manifest_path=manifest_path,
        version_req=version_req or None,
        extra=extra,
    )


def _dependency_name(requirement: str) -> str | None:
    name_chars: list[str] = []
    for character in requirement.strip():
        if character.isalnum() or character in {"_", ".", "-"}:
            name_chars.append(character)
            continue
        break
    name = "".join(name_chars)
    return name or None


def _test_facts(project_root: Path) -> list[TestFact]:
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        return []
    facts: list[TestFact] = []
    for path in sorted(tests_dir.rglob("*")):
        if not path.is_file() or path.suffix != PYTHON_SUFFIX:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(project_root).parts):
            continue
        function_count = _test_function_count(path)
        facts.append(
            TestFact(
                path=display_path(project_root, path),
                name=path.stem,
                function_count=function_count,
            )
        )
        if len(facts) >= TEST_LIMIT:
            break
    return facts


def _test_function_count(path: Path) -> int:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return 0
    return sum(
        1
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )
