"""Render Python package/build/test facts as semantic graph nodes."""

from __future__ import annotations

from typing import Any

from ._semantic_graph_fact_model import DependencyFact, ProjectFact, TestFact
from ._semantic_graph_fact_render import LANGUAGE_ID, PROVIDER_ID, stable_id


def project_graph_payload(
    project: ProjectFact | None,
) -> dict[str, list[dict[str, Any]]]:
    if project is None:
        return {"nodes": [], "edges": []}
    nodes = [_package_node(project), _build_node(project)]
    edges = [
        {
            "source": _package_id_for(project.package.name),
            "target": _build_id_for(project.package.name),
            "relation": "builds",
        }
    ]
    for dependency in project.dependencies:
        dependency_id = _dependency_id_for(project.package.name, dependency)
        nodes.append(_dependency_node(project, dependency, dependency_id))
        edges.append(
            {
                "source": _package_id_for(project.package.name),
                "target": dependency_id,
                "relation": "depends_on",
            }
        )
    for test in project.tests:
        test_id = _test_id_for(project.package.name, test)
        nodes.append(_test_node(project, test, test_id))
        edges.append(
            {
                "source": _build_id_for(project.package.name),
                "target": test_id,
                "relation": "tests",
            }
        )
        edges.append(
            {
                "source": test_id,
                "target": _package_id_for(project.package.name),
                "relation": "belongs_to",
            }
        )
    return {"nodes": nodes, "edges": edges}


def _package_node(project: ProjectFact) -> dict[str, Any]:
    manifest_path = project.package.manifest_path
    return {
        "id": _package_id_for(project.package.name),
        "kind": "package",
        "role": "python-project",
        "value": project.package.name,
        "action": "package",
        "path": manifest_path,
        "ownerPath": manifest_path,
        "startLine": 1,
        "endLine": 1,
        "locator": f"{manifest_path}:1:1",
        "matchText": project.package.name,
        "fields": {
            "languageId": LANGUAGE_ID,
            "providerId": PROVIDER_ID,
            "semanticFactKind": "package",
            "provenance": "parser",
            "confidence": "exact",
            "freshness": "fresh",
            "packageName": project.package.name,
            "manifestPath": manifest_path,
        },
    }


def _build_node(project: ProjectFact) -> dict[str, Any]:
    manifest_path = project.package.manifest_path
    command = _test_command()
    return {
        "id": _build_id_for(project.package.name),
        "kind": "build",
        "role": "pytest",
        "value": command,
        "action": "build",
        "path": manifest_path,
        "ownerPath": manifest_path,
        "startLine": 1,
        "endLine": 1,
        "locator": f"{manifest_path}:1:1",
        "matchText": command,
        "fields": {
            "languageId": LANGUAGE_ID,
            "providerId": PROVIDER_ID,
            "semanticFactKind": "build",
            "provenance": "build",
            "confidence": "exact",
            "freshness": "fresh",
            "packageName": project.package.name,
            "manifestPath": manifest_path,
            "tool": "pytest",
            "command": command,
        },
    }


def _dependency_node(
    project: ProjectFact,
    dependency: DependencyFact,
    dependency_id: str,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "languageId": LANGUAGE_ID,
        "providerId": PROVIDER_ID,
        "semanticFactKind": "dependency",
        "provenance": "parser",
        "confidence": "exact",
        "freshness": "fresh",
        "packageName": project.package.name,
        "manifestPath": dependency.manifest_path,
        "dependencyName": dependency.dependency_name,
        "dependencyPackageName": dependency.package_name,
        "dependencyKind": dependency.dependency_kind,
    }
    if dependency.version_req is not None:
        fields["versionReq"] = dependency.version_req
    if dependency.extra is not None:
        fields["extra"] = dependency.extra
    return {
        "id": dependency_id,
        "kind": "dependency",
        "role": dependency.dependency_kind,
        "value": dependency.package_name,
        "action": "deps",
        "path": dependency.manifest_path,
        "ownerPath": dependency.manifest_path,
        "startLine": 1,
        "endLine": 1,
        "locator": f"{dependency.manifest_path}:1:1",
        "matchText": dependency.package_name,
        "fields": fields,
    }


def _test_node(project: ProjectFact, test: TestFact, test_id: str) -> dict[str, Any]:
    return {
        "id": test_id,
        "kind": "test",
        "role": "pytest-target",
        "value": test.name,
        "action": "tests",
        "path": test.path,
        "ownerPath": test.path,
        "startLine": 1,
        "endLine": 1,
        "locator": f"{test.path}:1:1",
        "matchText": test.name,
        "fields": {
            "languageId": LANGUAGE_ID,
            "providerId": PROVIDER_ID,
            "semanticFactKind": "test",
            "provenance": "test",
            "confidence": "exact",
            "freshness": "fresh",
            "packageName": project.package.name,
            "testName": test.name,
            "testPath": test.path,
            "functionCount": test.function_count,
            "command": _test_command(),
        },
    }


def _package_id_for(package_name: str) -> str:
    return stable_id("package", package_name)


def _build_id_for(package_name: str) -> str:
    return stable_id("build", f"{_test_command()}:{package_name}")


def _dependency_id_for(package_name: str, dependency: DependencyFact) -> str:
    return stable_id(
        "dependency",
        f"{package_name}:{dependency.dependency_kind}:{dependency.package_name}",
    )


def _test_id_for(package_name: str, test: TestFact) -> str:
    return stable_id("test", f"{package_name}:{test.path}")


def _test_command() -> str:
    return "uv run --project . pytest"
