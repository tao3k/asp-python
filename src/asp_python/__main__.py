"""Module entrypoint for `python -m asp_python`."""

from __future__ import annotations

from ._cli import run_cli_from_env

raise SystemExit(run_cli_from_env())
