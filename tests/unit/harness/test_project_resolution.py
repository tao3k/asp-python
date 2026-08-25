"""Exercise candidate-bounded Python ProjectResolution parsing."""

from __future__ import annotations

import json
from pathlib import Path

from python_lang_project_harness._runtime import _response_frame


def request(candidate_paths: list[str]) -> dict[str, object]:
    return {
        "schemaId": "agent.semantic-protocols.provider-project-resolution-request",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "candidateBase": ".",
        "candidateGeneration": {
            "algorithm": "blake3-path-set-v1",
            "digest": "blake3:" + ("0" * 64),
            "authorities": ["asp-workspace-generation"],
        },
        "collectionScope": {"kind": "complete-generation"},
        "candidatePaths": candidate_paths,
        "policyExclusions": [],
    }


def project_resolution_frame(root: Path, payload: object) -> dict[str, object]:
    return _response_frame(
        {
            "schemaId": "agent.semantic-protocols.provider-runtime-request-frame",
            "schemaVersion": "1",
            "requestId": "project-resolution-test",
            "operation": "project-resolution",
            "payload": payload,
        },
        root,
    )


def run_project_resolution(root: Path, payload: object) -> dict[str, object]:
    frame = project_resolution_frame(root, payload)
    assert frame["outcome"] == "ready", frame
    result = frame["payload"]
    assert isinstance(result, dict)
    return result


def test_project_resolution_uses_only_candidates_and_uv_package_graph(
    tmp_path: Path,
) -> None:
    (tmp_path / "src/root_pkg").mkdir(parents=True)
    (tmp_path / "src/root_pkg/__init__.py").write_text("")
    (tmp_path / "src/root_pkg/untracked.py").write_text("")
    (tmp_path / "packages/member/src/member_pkg").mkdir(parents=True)
    (tmp_path / "packages/member/src/member_pkg/__init__.py").write_text("")
    (tmp_path / "examples/not-a-member/src/not_member").mkdir(parents=True)
    (tmp_path / "examples/not-a-member/src/not_member/__init__.py").write_text("")
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "root-package"
dependencies = ["requests>=2"]

[tool.uv.workspace]
members = ["packages/*"]

[tool.setuptools.package-dir]
"" = "src"
"""
    )
    (tmp_path / "packages/member/pyproject.toml").write_text(
        """
[project]
name = "member-package"

[tool.setuptools.package-dir]
"" = "src"
"""
    )
    (tmp_path / "examples/not-a-member/pyproject.toml").write_text(
        """
[project]
name = "not-a-member"

[tool.setuptools.package-dir]
"" = "src"
"""
    )

    response = run_project_resolution(
        tmp_path,
        request(
            [
                "pyproject.toml",
                "src/root_pkg/__init__.py",
                "packages/member/pyproject.toml",
                "packages/member/src/member_pkg/__init__.py",
                "examples/not-a-member/pyproject.toml",
                "examples/not-a-member/src/not_member/__init__.py",
            ]
        ),
    )

    assert response["state"] == "resolved"
    scope = response["scope"]
    assert scope["completeness"] == "exact"
    assert scope["candidateGenerationDigest"] == ("blake3:" + ("0" * 64))
    assert scope["metrics"] == {
        "parsedManifestCount": 2,
        "parsedLockfileCount": 0,
        "affectedPackageCount": 2,
        "fullWorkspaceReads": 0,
        "fullManifestReparses": 0,
        "dbOpens": 0,
        "elapsedMicros": 0,
    }
    scopes = scope["sourceScopes"]
    assert sorted(path for scope in scopes for path in scope["roots"]) == [
        "packages/member/src/member_pkg",
        "src/root_pkg",
    ]
    assert "src/root_pkg/untracked.py" not in json.dumps(response)
    assert sorted(path for scope in scopes for path in scope["explicitPaths"]) == [
        "packages/member/src/member_pkg",
        "src/root_pkg",
    ]
    assert scope["packageGraph"]["externalDependencies"][0]["name"] == "requests"
    assert all(
        package["name"] != "not-a-member"
        for package in scope["packageGraph"]["packages"]
    )


def test_setuptools_src_layout_is_package_manager_scope_without_provider_defaults(
    tmp_path: Path,
) -> None:
    (tmp_path / "src/example_pkg").mkdir(parents=True)
    (tmp_path / "src/example_pkg/__init__.py").write_text("")
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples/not_scope.py").write_text("")
    (tmp_path / "pyproject.toml").write_text(
        """
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "example-pkg"
"""
    )

    response = run_project_resolution(
        tmp_path,
        request(
            [
                "pyproject.toml",
                "src/example_pkg/__init__.py",
                "examples/not_scope.py",
            ]
        ),
    )

    scope = response["scope"]["sourceScopes"][0]
    assert scope["includeAuthority"] == "package-manager"
    assert scope["roots"] == ["src/example_pkg"]
    assert scope["explicitPaths"] == []
    assert all(
        not root.startswith("examples")
        for item in response["scope"]["sourceScopes"]
        for root in item["roots"]
    )


def test_project_resolution_rejects_non_object_request(tmp_path: Path) -> None:
    response = project_resolution_frame(tmp_path, [])
    assert response["outcome"] == "error"
    assert response["error"] == "provider runtime payload is not an object"


def test_project_resolution_requires_candidate_project_entry(tmp_path: Path) -> None:
    response = run_project_resolution(tmp_path, request(["src/pkg/__init__.py"]))
    assert response == {
        "schemaId": "agent.semantic-protocols.provider-project-resolution-response",
        "schemaVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "state": "not-applicable",
    }


def test_empty_uv_workspace_aggregator_is_not_a_provider_failure(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.uv]
package = false

[tool.uv.workspace]
members = ["packages/python"]
exclude = ["packages/python"]
"""
    )

    response = run_project_resolution(tmp_path, request(["pyproject.toml"]))

    assert response["state"] == "resolved"
    scope = response["scope"]
    assert scope["state"] == "resolved"
    assert scope["completeness"] == "exact"
    assert scope["projectEntry"] == "pyproject.toml"
    assert scope["packageGraph"]["packages"] == []
    assert scope["sourceScopes"] == []
    assert scope["metrics"]["fullWorkspaceReads"] == 0
    assert scope["metrics"]["dbOpens"] == 0


def test_provider_registration_advertises_project_resolution() -> None:
    project_root = Path(__file__).parents[3]
    manifest = json.loads(
        (project_root / "provider/asp-provider-registration.json").read_text()
    )
    descriptor = manifest["sourceInventory"]["projectResolution"]
    assert descriptor == {"entryMarkers": ["pyproject.toml"]}

    operations = {
        operation["operation"]: operation
        for operation in manifest["runtimeContract"]["operations"]
    }
    project_resolution = operations["project-resolution"]
    assert project_resolution["requestSchemaId"].endswith(
        "/provider-project-resolution-request.schema.json"
    )
    assert project_resolution["responseSchemaId"].endswith(
        "/provider-project-resolution-response.schema.json"
    )


def test_explicit_owner_collection_scope_is_required_and_normalized(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "fixture"\n')
    payload = request(["pyproject.toml"])
    payload["collectionScope"] = {
        "kind": "explicit-owners",
        "ownerPaths": ["src/changed.py"],
    }
    assert run_project_resolution(tmp_path, payload)["state"] == "resolved"

    payload["collectionScope"] = {
        "kind": "explicit-owners",
        "ownerPaths": ["src/../changed.py"],
    }
    failure = project_resolution_frame(tmp_path, payload)
    assert failure["outcome"] == "error"
    assert "normalized workspace-relative" in failure["error"]
