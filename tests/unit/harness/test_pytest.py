from __future__ import annotations

from typing import TYPE_CHECKING

from python_lang_parser import PythonDiagnosticSeverity
from python_lang_project_harness import PythonHarnessConfig, python_project_harness_test
from python_lang_project_harness.pytest import (
    python_project_harness_test as facade_python_project_harness_test,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_python_project_harness_test_returns_pytest_collectable_callable(
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

    harness_test = python_project_harness_test(tmp_path)

    assert harness_test.__name__ == "test_python_project_harness_policy"
    assert harness_test.__qualname__ == "test_python_project_harness_policy"
    harness_test()


def test_python_project_harness_test_defaults_to_current_project_root(
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

    harness_test = python_project_harness_test()

    harness_test()


def test_public_pytest_facade_exposes_collectable_helper() -> None:
    assert facade_python_project_harness_test is python_project_harness_test


def test_python_project_harness_test_blocks_with_compact_snapshot(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "library.py"
    source.write_text('def run() -> None:\n    print("debug")\n', encoding="utf-8")
    harness_test = python_project_harness_test(tmp_path)

    try:
        harness_test()
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("pytest harness callable should block policy findings")

    assert "rule=PY-MOD-R002 severity=warning" in message
    assert "|message Library module uses bare print" in message
    assert "src/library.py" in message
    assert str(source) not in message
    assert "[advice]" in message


def test_python_project_harness_test_can_disable_agent_advice(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "library.py"
    source.write_text('def run() -> None:\n    print("debug")\n', encoding="utf-8")
    harness_test = python_project_harness_test(tmp_path, include_advice=False)

    try:
        harness_test()
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("pytest harness callable should block policy findings")

    assert "rule=PY-MOD-R002 severity=warning" in message
    assert "|message Library module uses bare print" in message
    assert "[advice]" not in message


def test_python_project_harness_test_honors_embedded_options(
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

    harness_test = python_project_harness_test(
        tmp_path,
        severities=frozenset({PythonDiagnosticSeverity.ERROR}),
        include_tests=False,
        source_dir_names=("lib",),
        test_name="test_custom_python_project_policy",
    )

    assert harness_test.__name__ == "test_custom_python_project_policy"
    assert harness_test.__qualname__ == "test_custom_python_project_policy"
    harness_test()


def test_python_project_harness_test_honors_configured_project_resolution(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    tests = tmp_path / "tests" / "unit"
    lib.mkdir()
    tests.mkdir(parents=True)
    (lib / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    harness_test = python_project_harness_test(
        tmp_path,
        config=PythonHarnessConfig(source_dir_names=("lib",), include_tests=False),
    )

    harness_test()


def test_python_project_harness_test_honors_extra_project_paths(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tools = tmp_path / "tools"
    src.mkdir()
    tools.mkdir()
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tools / "check.py").write_text('"""Check docs."""\n', encoding="utf-8")

    harness_test = python_project_harness_test(
        tmp_path,
        extra_path_names=("tools",),
    )

    harness_test()
