from __future__ import annotations

import re
from pathlib import Path

from python_lang_project_harness._dependency_topology import (
    build_dependency_topology_packet,
)


def test_dependency_topology_packet_projects_pyproject_dependencies(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "fixture"
version = "0.1.0"
dependencies = ["requests>=2.31", "typing-extensions==4.12.2"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    packet = build_dependency_topology_packet(tmp_path)

    assert packet["packetKind"] == "dependency-topology"
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", packet["fingerprint"])
    graph = packet["graph"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes["dependency:requests"] == {
        "id": "dependency:requests",
        "kind": "dependency",
        "value": "requests",
        "path": "pyproject.toml",
        "fields": {
            "dependencyName": "requests",
            "manifestPath": "pyproject.toml",
        },
    }
    assert nodes["dependency-version:requests"]["fields"]["version"] == ">=2.31"
    assert {
        "source": "dependency:requests",
        "target": "dependency-version:requests",
        "relation": "version_locked",
    } in graph["edges"]


def test_dependency_topology_packet_projects_requirements_files(
    tmp_path: Path,
) -> None:
    requirements_dir = tmp_path / "requirements"
    requirements_dir.mkdir()
    (requirements_dir / "runtime.txt").write_text(
        """
# Runtime dependencies
Requests[security]~=2.32 ; python_version >= "3.11"
urllib3==2.2.2  # pinned by deployment image
-r generated.txt
git+https://example.invalid/acme.git
""".strip()
        + "\n",
        encoding="utf-8",
    )

    packet = build_dependency_topology_packet(tmp_path)

    graph = packet["graph"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes["dependency:requests"]["path"] == "requirements/runtime.txt"
    assert nodes["dependency-version:requests"]["value"] == "~=2.32"
    assert nodes["dependency-version:urllib3"]["value"] == "==2.2.2"
    assert all("generated" not in node["id"] for node in graph["nodes"])


def test_dependency_topology_fingerprint_is_stable(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "requests>=2.31\nurllib3==2.2.2\n",
        encoding="utf-8",
    )

    first = build_dependency_topology_packet(tmp_path)
    second = build_dependency_topology_packet(tmp_path)

    assert first == second
