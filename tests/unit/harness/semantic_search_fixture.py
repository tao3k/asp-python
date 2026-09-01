"""Fixtures for semantic-search CLI tests."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from asp_python._semantic_search_graph_render import (
    SEMANTIC_AGENT_PROTOCOL_BIN_ENV,
)


def compact_graph_renderer_available() -> bool:
    configured_bin = os.environ.get(SEMANTIC_AGENT_PROTOCOL_BIN_ENV)
    if configured_bin is not None:
        return Path(configured_bin).exists()
    return shutil.which("asp") is not None


def require_compact_graph_renderer() -> None:
    if not compact_graph_renderer_available():
        pytest.skip("asp graph renderer is not available")


def write_search_fixture(project_root: Path) -> None:
    package = project_root / "src" / "pkg"
    tests = project_root / "tests"
    package.mkdir(parents=True)
    tests.mkdir()
    (project_root / "pyproject.toml").write_text(
        """
[project]
name = "demo-python"
version = "0.1.0"
import-names = ["pkg"]
dependencies = ["requests>=2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""".lstrip(),
        encoding="utf-8",
    )
    (package / "__init__.py").write_text(
        '"""Package owner."""\n\nfrom .service import build\n\n__all__ = ("build",)\n',
        encoding="utf-8",
    )
    (package / "service.py").write_text(
        '"""Service owner."""\n\n'
        "import requests\n"
        "from requests import Response\n\n"
        "class SessionClient(requests.Session):\n"
        "    pass\n\n"
        "def fetch() -> Response:\n"
        "    return Response()\n\n"
        "def build(value: str) -> str:\n"
        "    return value.strip()\n",
        encoding="utf-8",
    )
    (tests / "test_service.py").write_text(
        "from pkg.service import build\n\n"
        "def test_build() -> None:\n"
        "    assert build(' ok ') == 'ok'\n",
        encoding="utf-8",
    )
