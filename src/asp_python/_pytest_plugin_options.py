"""Option registration and typed configuration for the pytest integration."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

from ._model import AspPythonConfig
from ._project_config import read_asp_python_config
from ._pytest_plugin_project import project_root

if TYPE_CHECKING:
    from collections.abc import Sequence


ENABLE_OPTION = "--python-project-harness"
NO_TESTS_OPTION = "--python-project-harness-no-tests"
SOURCE_DIR_OPTION = "--python-project-harness-source-dir"
TEST_DIR_OPTION = "--python-project-harness-test-dir"
EXTRA_PATH_OPTION = "--python-project-harness-extra-path"
NO_ADVICE_OPTION = "--python-project-harness-no-advice"

_ROOT_OPTION = "--python-project-harness-root"
_DISABLE_RULE_OPTION = "--python-project-harness-disable-rule"
_BLOCK_RULE_OPTION = "--python-project-harness-block-rule"
_ERROR_ONLY_OPTION = "--python-project-harness-error-only"


def add_options(parser: pytest.Parser) -> None:
    """Register Python project harness pytest options."""

    group = parser.getgroup("asp-python")
    for name, kwargs in (
        (
            ENABLE_OPTION,
            {
                "action": "store_true",
                "default": False,
                "help": "Collect and run the asp-python policy test.",
            },
        ),
        (
            _ROOT_OPTION,
            {
                "action": "store",
                "default": None,
                "metavar": "PATH",
                "help": "Project root for the harness test. Defaults to pytest rootdir.",
            },
        ),
        (
            NO_TESTS_OPTION,
            {
                "action": "store_true",
                "default": False,
                "help": "Do not parse test files; pytest layout checks still run.",
            },
        ),
        (
            SOURCE_DIR_OPTION,
            {
                "action": "append",
                "default": [],
                "metavar": "NAME",
                "help": "Source directory name to scan. Can be provided more than once.",
            },
        ),
        (
            TEST_DIR_OPTION,
            {
                "action": "append",
                "default": [],
                "metavar": "NAME",
                "help": "Test directory name to scan. Can be provided more than once.",
            },
        ),
        (
            EXTRA_PATH_OPTION,
            {
                "action": "append",
                "default": [],
                "metavar": "NAME",
                "help": "Extra project path name to scan. Can be provided more than once.",
            },
        ),
        (
            _DISABLE_RULE_OPTION,
            {
                "action": "append",
                "default": [],
                "metavar": "RULE_ID",
                "help": "Harness rule id to suppress. Can be provided more than once.",
            },
        ),
        (
            _BLOCK_RULE_OPTION,
            {
                "action": "append",
                "default": [],
                "metavar": "RULE_ID",
                "help": "Harness rule id to treat as blocking. Can be provided more than once.",
            },
        ),
        (
            _ERROR_ONLY_OPTION,
            {
                "action": "store_true",
                "default": False,
                "help": "Only fail the pytest harness item for parser errors.",
            },
        ),
        (
            NO_ADVICE_OPTION,
            {
                "action": "store_true",
                "default": False,
                "help": "Hide non-blocking advice from assertion output.",
            },
        ),
    ):
        group.addoption(name, **kwargs)


def blocking_severities(
    config: pytest.Config,
) -> frozenset[PythonDiagnosticSeverity] | None:
    if config.getoption(_ERROR_ONLY_OPTION):
        return frozenset({PythonDiagnosticSeverity.ERROR})
    return None


def harness_config(config: pytest.Config) -> AspPythonConfig | None:
    disabled_rule_values = config.getoption(_DISABLE_RULE_OPTION)
    blocking_rule_values = config.getoption(_BLOCK_RULE_OPTION)
    if not disabled_rule_values and not blocking_rule_values:
        return None

    base_config = read_asp_python_config(project_root(config))
    selected_config = base_config if base_config is not None else AspPythonConfig()
    return replace(
        selected_config,
        disabled_rule_ids=(
            frozenset(disabled_rule_values)
            if disabled_rule_values
            else selected_config.disabled_rule_ids
        ),
        blocking_rule_ids=(
            frozenset(blocking_rule_values)
            if blocking_rule_values
            else selected_config.blocking_rule_ids
        ),
    )


def optional_tuple(values: Sequence[str]) -> tuple[str, ...] | None:
    return tuple(values) if values else None
