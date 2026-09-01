"""Installed package identity for the Python project harness."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

_DISTRIBUTION_NAME: Final = "asp-python"


def _installed_version() -> str:
    try:
        return version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return "0.0.0+unknown"


__version__: Final = _installed_version()
