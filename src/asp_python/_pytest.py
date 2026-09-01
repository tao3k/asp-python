"""Pytest-facing helpers for embedding the Python project harness."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._runner import assert_asp_python_clean

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from python_lang_parser import PythonDiagnosticSeverity

    from ._model import AspPythonConfig, PythonLangRulePack


def asp_python_test(
    project_root: str | Path = ".",
    *,
    config: AspPythonConfig | None = None,
    rule_packs: Sequence[PythonLangRulePack] | None = None,
    severities: frozenset[PythonDiagnosticSeverity] | None = None,
    include_tests: bool | None = None,
    source_dir_names: Sequence[str] | None = None,
    test_dir_names: Sequence[str] | None = None,
    extra_path_names: Sequence[str] | None = None,
    test_name: str = "test_asp_python_policy",
    include_advice: bool = True,
) -> Callable[[], None]:
    """Return a pytest-collectable test function for one Python project."""

    root = Path(project_root)

    def test_asp_python_policy() -> None:
        assert_asp_python_clean(
            root,
            config=config,
            rule_packs=rule_packs,
            severities=severities,
            include_tests=include_tests,
            source_dir_names=source_dir_names,
            test_dir_names=test_dir_names,
            extra_path_names=extra_path_names,
            include_advice=include_advice,
        )

    test_asp_python_policy.__name__ = test_name
    test_asp_python_policy.__qualname__ = test_name
    test_asp_python_policy.__doc__ = (
        "Run the Python project harness over configured project paths."
    )
    return test_asp_python_policy
