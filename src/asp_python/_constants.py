"""Shared constants for the Python language harness."""

from __future__ import annotations

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

IGNORED_DIR_NAMES = frozenset(
    {
        ".git",
        ".cache",
        ".data",
        ".devenv",
        ".direnv",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".run",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "result",
        "target",
        "venv",
    }
)
INCLUDE_HIDDEN_DIR_NAMES = frozenset[str]()
DEFAULT_BLOCKING_SEVERITIES = frozenset(
    {
        PythonDiagnosticSeverity.ERROR,
        PythonDiagnosticSeverity.WARNING,
    }
)
