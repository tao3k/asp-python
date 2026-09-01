"""Configurable pytest layout exceptions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TEST_LAYOUT_POLICY_CONFIG = "python-project-harness-rules.toml"


@dataclass(frozen=True, slots=True)
class PythonTestLayoutPolicy:
    """Explained tests-root exceptions loaded from project-local TOML."""

    allowed_root_files: frozenset[str] = frozenset()
    allowed_directories: frozenset[str] = frozenset()

    def allows_root_file(self, name: str) -> bool:
        """Return whether a root-level test file has an explained exception."""

        return name in self.allowed_root_files

    def allows_directory(self, name: str) -> bool:
        """Return whether a tests-root directory has an explained exception."""

        return name in self.allowed_directories


def load_test_layout_policy(tests_dir: Path) -> PythonTestLayoutPolicy:
    """Load explained pytest layout exceptions from a tests-root config file."""

    config_path = tests_dir / TEST_LAYOUT_POLICY_CONFIG
    if not config_path.is_file():
        return PythonTestLayoutPolicy()

    try:
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return PythonTestLayoutPolicy()

    tests_table = payload.get("tests")
    if not isinstance(tests_table, dict):
        return PythonTestLayoutPolicy()

    return PythonTestLayoutPolicy(
        allowed_root_files=_explained_names(tests_table.get("allowed_root_files")),
        allowed_directories=_explained_names(tests_table.get("allowed_directories")),
    )


def _explained_names(raw_entries: Any) -> frozenset[str]:
    if not isinstance(raw_entries, list):
        return frozenset()

    names: set[str] = set()
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        explanation = entry.get("explanation")
        if not _has_text(name) or not _has_text(explanation):
            continue
        names.add(name.strip())
    return frozenset(names)


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
