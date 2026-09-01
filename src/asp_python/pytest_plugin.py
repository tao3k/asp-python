"""Pytest plugin entry point for dev-dependency harness mounting."""

from __future__ import annotations

from pathlib import Path

import pytest

from ._pytest_plugin_options import (
    ENABLE_OPTION,
    EXTRA_PATH_OPTION,
    NO_ADVICE_OPTION,
    NO_TESTS_OPTION,
    SOURCE_DIR_OPTION,
    TEST_DIR_OPTION,
    add_options,
    blocking_severities,
    harness_config,
    optional_tuple,
)
from ._pytest_plugin_project import project_root
from ._runner import assert_asp_python_clean


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register Python project harness pytest options."""

    add_options(parser)


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Insert one explicit harness item when the plugin option is enabled."""

    if not config.getoption(ENABLE_OPTION):
        return
    item = PythonProjectHarnessItem.from_parent(
        session,
        name="python-project-harness",
        nodeid="python-project-harness",
    )
    items.insert(0, item)


class PythonProjectHarnessItem(pytest.Item):
    """Pytest item that runs the parser-backed project harness."""

    def runtest(self) -> None:
        """Run the configured project harness and raise a compact assertion."""

        assert_asp_python_clean(
            project_root(self.config),
            config=harness_config(self.config),
            severities=blocking_severities(self.config),
            include_tests=not self.config.getoption(NO_TESTS_OPTION),
            source_dir_names=optional_tuple(self.config.getoption(SOURCE_DIR_OPTION)),
            test_dir_names=optional_tuple(self.config.getoption(TEST_DIR_OPTION)),
            extra_path_names=optional_tuple(self.config.getoption(EXTRA_PATH_OPTION)),
            include_advice=not self.config.getoption(NO_ADVICE_OPTION),
        )

    def repr_failure(
        self,
        excinfo: pytest.ExceptionInfo[BaseException],
        style: str | None = None,
    ) -> str:
        """Return compact harness assertion text without pytest traceback noise."""

        if isinstance(excinfo.value, AssertionError):
            return str(excinfo.value)
        return super().repr_failure(excinfo, style=style)

    def reportinfo(self) -> tuple[Path, int, str]:
        """Return stable report metadata for pytest output."""

        return (Path("python-project-harness"), 0, "python project harness")
