"""Python package-manager workspace scope fast-path tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from python_lang_project_harness import python_semantic_language_registration, run_cli


def test_workspace_scope_is_json_fast_path_and_registry_contract(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "scope-root"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    stdout = io.StringIO()

    assert (
        run_cli(
            ["search", "workspace-scope", "--json", "--workspace", str(tmp_path)],
            stdout=stdout,
            cwd=tmp_path,
        )
        == 0
    )

    payload = json.loads(stdout.getvalue())
    assert payload["schemaId"] == "agent.semantic-protocols.semantic-workspace-scope"
    assert payload["schemaVersion"] == "1"
    assert payload["fingerprint"].startswith("sha256:")
    assert payload["workspaceId"] == "python:scope-root"
    assert payload["packageManager"] == "uv"
    assert payload["sourceExtensions"] == [".py", ".pyi"]
    assert payload["discoveryRoot"] == tmp_path.resolve().as_posix()
    assert payload["admittedRoots"] == [tmp_path.resolve().as_posix()]
    assert {anchor["kind"] for anchor in payload["anchors"]} == {
        "pyproject",
        "python-lock",
    }

    registration = python_semantic_language_registration()
    descriptor = next(
        item
        for item in registration["methodDescriptors"]
        if item["method"] == "search/workspace-scope"
    )
    assert descriptor["outputSchemaIds"] == [
        "agent.semantic-protocols.semantic-workspace-scope"
    ]
    assert descriptor["outputModes"] == ["json"]
    assert any(
        schema["schemaId"] == "agent.semantic-protocols.semantic-workspace-scope"
        and schema["path"] == "schemas/semantic-workspace-scope.v1.schema.json"
        for schema in registration["schemas"]
    )


def test_workspace_scope_admits_uv_member_outside_discovery_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    sibling = tmp_path / "shared"
    root.mkdir()
    sibling.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "scope-root"\nversion = "0.1.0"\n'
        '[tool.uv.workspace]\nmembers = ["../shared"]\n',
        encoding="utf-8",
    )
    (sibling / "pyproject.toml").write_text(
        '[project]\nname = "shared-member"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    stdout = io.StringIO()

    assert (
        run_cli(
            ["search", "workspace-scope", "--json", "--workspace", str(root)],
            stdout=stdout,
            cwd=root,
        )
        == 0
    )

    payload = json.loads(stdout.getvalue())
    assert payload["schemaId"] == "agent.semantic-protocols.semantic-workspace-scope"
    assert payload["admittedRoots"] == sorted(
        [root.resolve().as_posix(), sibling.resolve().as_posix()]
    )
    assert {package["name"] for package in payload["packages"]} == {
        "scope-root",
        "shared-member",
    }


def test_workspace_scope_rejects_compact_mode(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "scope-root"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    assert (
        run_cli(
            ["search", "workspace-scope", "--workspace", str(tmp_path)],
            stdout=stdout,
            stderr=stderr,
            cwd=tmp_path,
        )
        == 3
    )
    assert "requires --json" in stderr.getvalue()


def test_provider_manifest_advertises_workspace_scope_capability() -> None:
    manifest_path = Path(__file__).parents[3] / "provider/asp-provider-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["searchCapabilities"]["workspaceScope"] is True
