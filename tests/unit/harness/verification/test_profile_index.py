from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    PythonOwnerResponsibility,
    PythonVerificationProfileHint,
    build_python_verification_profile_index_with_config,
    default_python_harness_config,
    render_python_verification_profile_index,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_profile_index_aggregates_public_branch_owners(tmp_path: Path) -> None:
    _write_public_branch_project(tmp_path)

    index = build_python_verification_profile_index_with_config(
        tmp_path,
        default_python_harness_config(),
    )
    rendered = render_python_verification_profile_index(index)

    assert index.needs_profile_configuration()
    assert "[verify-profile] profile_hints" in rendered
    assert "   |state: missing_profile_config" in rendered
    assert "   |action: configure PythonVerificationProfileHint entries" in rendered
    assert "   |candidates: 1" in rendered
    assert "[verify-profile] src/pkg/__init__.py" in rendered
    assert "[verify-profile] src/pkg/alpha.py" not in rendered
    assert "[verify-profile] src/pkg/beta.py" not in rendered


def test_profile_index_renders_configured_responsibilities_for_drift(
    tmp_path: Path,
) -> None:
    _write_public_branch_project(tmp_path)
    config = default_python_harness_config().with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/__init__.py",
            (PythonOwnerResponsibility.CLI,),
        )
    )

    index = build_python_verification_profile_index_with_config(tmp_path, config)
    rendered = render_python_verification_profile_index(index)
    candidate = index.active_candidates()[0]

    assert not index.needs_profile_configuration()
    assert candidate.state == "profile_drift"
    assert candidate.configured_responsibilities == (PythonOwnerResponsibility.CLI,)
    assert "[verify-profile] profile_hints" not in rendered
    assert "   |configured: cli" in rendered
    assert "   |suggest: public_api" in rendered
    assert not index.is_clear()


def test_profile_index_omits_configured_candidates(tmp_path: Path) -> None:
    _write_public_branch_project(tmp_path)
    config = default_python_harness_config().with_verification_profile_hint(
        PythonVerificationProfileHint(
            "src/pkg/__init__.py",
            (PythonOwnerResponsibility.PUBLIC_API,),
        )
    )

    index = build_python_verification_profile_index_with_config(tmp_path, config)

    assert index.is_clear()
    assert not index.needs_profile_configuration()
    assert index.active_candidates() == ()
    assert render_python_verification_profile_index(index) == ""


def _write_public_branch_project(project_root: Path) -> None:
    package = project_root / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Package docs."""\n__all__ = ["Alpha", "Beta"]\n'
        "from .alpha import Alpha\nfrom .beta import Beta\n",
        encoding="utf-8",
    )
    (package / "alpha.py").write_text(
        '"""Alpha API."""\n\nclass Alpha:\n    pass\n',
        encoding="utf-8",
    )
    (package / "beta.py").write_text(
        '"""Beta API."""\n\nclass Beta:\n    pass\n',
        encoding="utf-8",
    )
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
