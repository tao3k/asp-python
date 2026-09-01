from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    default_python_harness_config,
    render_asp_python_agent_snapshot_with_config,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_agent_snapshot_reminds_when_verification_profile_is_unconfigured(
    tmp_path: Path,
) -> None:
    _write_public_api_project(tmp_path)

    rendered = render_asp_python_agent_snapshot_with_config(
        tmp_path,
        default_python_harness_config(),
    )

    assert "[verify-profile] profile_hints" in rendered
    assert "   |state: missing_profile_config" in rendered
    assert "   |action: configure PythonVerificationProfileHint entries" in rendered
    assert "[verify-profile] src/pkg/api.py" in rendered


def _write_public_api_project(project_root: Path) -> None:
    package = project_root / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package docs."""\n__all__ = ["build"]\nfrom .api import build\n',
        encoding="utf-8",
    )
    (package / "api.py").write_text(
        '"""Public API."""\n\n\ndef build(value: int) -> int:\n    return value\n',
        encoding="utf-8",
    )
    (package / "py.typed").write_text("", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        """
[project]
name = "pkg"
requires-python = ">=3.12"
import-names = ["pkg"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pkg"]
""".lstrip(),
        encoding="utf-8",
    )
