"""Provider-native Python project fixtures."""

from __future__ import annotations

from pathlib import Path


def write_python_project_fixture(project_root: Path) -> None:
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
