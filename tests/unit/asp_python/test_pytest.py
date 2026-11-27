from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import AspPythonConfig, asp_python_test
from asp_python.pytest import (
    asp_python_test as facade_asp_python_test,
)
from python_lang_parser import PythonDiagnosticSeverity

if TYPE_CHECKING:
    from pathlib import Path


def test_asp_python_test_returns_pytest_collectable_callable(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text(
        '"""Library docs."""\n\nVALUE = 1\n', encoding="utf-8"
    )
    (tests / "test_library.py").write_text(
        "def test_value() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    asp_python_test_case = asp_python_test(tmp_path)

    assert asp_python_test_case.__name__ == "test_asp_python_policy"
    assert asp_python_test_case.__qualname__ == "test_asp_python_policy"
    asp_python_test_case()


def test_asp_python_test_defaults_to_current_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tests / "test_library.py").write_text(
        "def test_value() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    asp_python_test_case = asp_python_test()

    asp_python_test_case()


def test_public_pytest_facade_exposes_collectable_helper() -> None:
    assert facade_asp_python_test is asp_python_test


def test_asp_python_test_blocks_with_compact_snapshot(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "library.py"
    source.write_text('def run() -> None:\n    print("debug")\n', encoding="utf-8")
    asp_python_test_case = asp_python_test(tmp_path)

    try:
        asp_python_test_case()
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("ASP Python pytest callable should block policy findings")

    assert "rule=PY-MOD-R002 severity=warning" in message
    assert "|message Library module uses bare print" in message
    assert "src/library.py" in message
    assert str(source) not in message
    assert "[advice]" in message


def test_asp_python_test_can_disable_agent_advice(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "library.py"
    source.write_text('def run() -> None:\n    print("debug")\n', encoding="utf-8")
    asp_python_test_case = asp_python_test(tmp_path, include_advice=False)

    try:
        asp_python_test_case()
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("ASP Python pytest callable should block policy findings")

    assert "rule=PY-MOD-R002 severity=warning" in message
    assert "|message Library module uses bare print" in message
    assert "[advice]" not in message


def test_asp_python_test_honors_embedded_options(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    tests = tmp_path / "tests" / "unit"
    lib.mkdir()
    tests.mkdir(parents=True)
    (lib / "library.py").write_text(
        'def run() -> None:\n    print("debug")\n',
        encoding="utf-8",
    )
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    asp_python_test_case = asp_python_test(
        tmp_path,
        severities=frozenset({PythonDiagnosticSeverity.ERROR}),
        include_tests=False,
        source_dir_names=("lib",),
        test_name="test_custom_python_project_policy",
    )

    assert asp_python_test_case.__name__ == "test_custom_python_project_policy"
    assert asp_python_test_case.__qualname__ == "test_custom_python_project_policy"
    asp_python_test_case()


def test_asp_python_test_honors_configured_project_resolution(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    tests = tmp_path / "tests" / "unit"
    lib.mkdir()
    tests.mkdir(parents=True)
    (lib / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    asp_python_test_case = asp_python_test(
        tmp_path,
        config=AspPythonConfig(source_dir_names=("lib",), include_tests=False),
    )

    asp_python_test_case()


def test_asp_python_test_honors_extra_project_paths(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tools = tmp_path / "tools"
    src.mkdir()
    tools.mkdir()
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tools / "check.py").write_text('"""Check docs."""\n', encoding="utf-8")

    asp_python_test_case = asp_python_test(
        tmp_path,
        extra_path_names=("tools",),
    )

    asp_python_test_case()
