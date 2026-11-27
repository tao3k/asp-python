from __future__ import annotations

from pathlib import Path

from asp_python import asp_python_test

_PROJECT_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").exists() and (parent / "src").exists()
)


test_asp_python_self_policy = asp_python_test(_PROJECT_ROOT)
