from __future__ import annotations

from typing import TYPE_CHECKING

from asp_python import (
    PythonModularityRulePack,
    PythonTestLayoutRulePack,
    asp_python_paths,
    asp_python_scope,
    assert_asp_python_clean,
    python_modularity_rules,
    python_test_layout_rules,
    run_asp_python,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_asp_python_paths_use_project_root_by_default(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests"
    src.mkdir()
    tests.mkdir()

    assert asp_python_paths(tmp_path) == (tmp_path,)
    assert asp_python_paths(tmp_path, include_tests=False) == (src,)


def test_asp_python_scope_exposes_project_and_classification_paths(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests"
    src.mkdir()
    tests.mkdir()

    scope = asp_python_scope(tmp_path)

    assert scope.source_paths == (src,)
    assert scope.test_paths == (tests,)
    assert scope.extra_paths == ()
    assert scope.project_paths == (tmp_path,)
    assert scope.monitored_paths == (tmp_path,)
    assert scope.to_dict()["monitored_paths"] == [str(tmp_path)]


def test_asp_python_paths_fall_back_to_root(tmp_path: Path) -> None:
    module = tmp_path / "module.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")

    assert asp_python_paths(tmp_path) == (tmp_path,)


def test_run_asp_python_uses_project_paths(tmp_path: Path) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tests / "test_library.py").write_text(
        "def test_value() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert report.is_clean
    assert report.file_count == 2
    assert report.root_paths == (str(tmp_path),)
    assert report.project_resolution is not None
    assert report.to_dict()["project_resolution"] == {
        "project_root": str(tmp_path),
        "project_metadata": None,
        "project_paths": [str(tmp_path)],
        "source_paths": [str(src)],
        "test_paths": [str(tests.parent)],
        "extra_paths": [],
        "include_tests": True,
        "monitored_paths": [str(tmp_path)],
    }


def test_run_asp_python_monitors_src_and_tests_by_default(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src" / "pkg"
    tests = tmp_path / "tests" / "unit"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    source_file = src / "library.py"
    test_file = tests / "test_library.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    test_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [module.path for module in report.modules] == [
        str(source_file),
        str(test_file),
    ]
    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("python.syntax.invalid", str(test_file)),
    ]


def test_run_asp_python_can_exclude_tests_from_scope(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests" / "unit"
    src.mkdir()
    tests.mkdir(parents=True)
    (src / "library.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tests / "test_scattered.py").write_text(
        "def broken(:\n    pass\n",
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path, include_tests=False)

    assert report.is_clean
    assert [module.path for module in report.modules] == [str(src / "library.py")]
    assert report.project_resolution is not None
    assert report.project_resolution.test_paths == (tests.parent,)
    assert report.project_resolution.monitored_paths == (src,)


def test_run_asp_python_does_not_fallback_into_excluded_tests(
    tmp_path: Path,
) -> None:
    package = tmp_path / "pkg"
    tests = tmp_path / "tests" / "unit"
    package.mkdir()
    tests.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Package docs."""\n', encoding="utf-8")
    (tests / "test_bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    report = run_asp_python(tmp_path, include_tests=False)

    assert report.is_clean
    assert [module.path for module in report.modules] == [str(package / "__init__.py")]
    assert report.project_resolution is not None
    assert report.project_resolution.project_paths == (package,)


def test_include_tests_false_skips_test_parsing_not_layout_policy(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    tests = tmp_path / "tests"
    src.mkdir()
    tests.mkdir()
    (src / "library.py").write_text('"""Library docs."""\n', encoding="utf-8")
    (tests / "test_scattered.py").write_text(
        "def broken(:\n    pass\n",
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path, include_tests=False)

    assert report.file_count == 1
    assert [finding.rule_id for finding in report.findings] == ["PY-TEST-R001"]
    assert report.project_resolution is not None
    assert report.project_resolution.monitored_paths == (src,)


def test_assert_asp_python_clean_blocks_for_pytest(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "library.py"
    source.write_text('def run() -> None:\n    print("debug")\n', encoding="utf-8")

    try:
        assert_asp_python_clean(tmp_path)
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("project harness should block package warnings")

    assert "rule=PY-MOD-R002 severity=warning" in message
    assert "|message Library module uses bare print" in message
    assert "src/library.py" in message
    assert str(source) not in message


def test_project_harness_blocks_root_pytest_files(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    source = tests / "test_scattered.py"
    source.write_text(
        "def test_scattered() -> None:\n    assert True\n", encoding="utf-8"
    )

    try:
        assert_asp_python_clean(tmp_path)
    except AssertionError as error:
        message = str(error)
    else:
        raise AssertionError("project harness should block root pytest files")

    assert "rule=PY-TEST-R001 severity=warning" in message
    assert "|message Pytest file is scattered in tests root" in message
    assert "tests/unit/" in message
    assert "tests/test_scattered.py" in message
    assert str(source) not in message


def test_project_harness_blocks_unexpected_tests_root_entries(tmp_path: Path) -> None:
    unexpected = tmp_path / "tests" / "misc"
    unexpected.mkdir(parents=True)

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-TEST-R002", str(unexpected)),
    ]


def test_project_harness_blocks_bloated_unit_test_leaf(tmp_path: Path) -> None:
    unit = tmp_path / "tests" / "unit"
    unit.mkdir(parents=True)
    source = unit / "test_large_policy.py"
    source.write_text(_large_unit_test_source(), encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-TEST-R003", str(source)),
    ]
    assert "folder-first unit suite" in report.findings[0].requirement


def test_test_layout_rule_pack_descriptor_and_catalog_are_stable() -> None:
    descriptor = PythonTestLayoutRulePack().descriptor()
    rules = python_test_layout_rules()

    assert descriptor.id == "python.test_layout"
    assert descriptor.to_dict()["domains"] == ["pytest-layout", "unit-tests", "python"]
    assert [rule.rule_id for rule in rules] == [
        "PY-TEST-R001",
        "PY-TEST-R002",
        "PY-TEST-R003",
    ]


def test_modularity_rule_pack_blocks_bloated_multi_responsibility_module(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    source = src / "feature.py"
    source.write_text(_large_multi_responsibility_module_source(), encoding="utf-8")

    report = run_asp_python(tmp_path)

    assert [
        (finding.rule_id, finding.location.path) for finding in report.findings
    ] == [
        ("PY-MOD-R006", str(source)),
    ]
    assert "ownership seams" in report.findings[0].label


def test_modularity_rule_pack_accepts_compact_module(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        """
\"\"\"Service helpers for tests.\"\"\"


class Service:
    def __init__(self, value: int) -> None:
        self.value = value

    def get_value(self) -> int:
        return self.value
""",
        encoding="utf-8",
    )

    report = run_asp_python(tmp_path)

    assert report.is_clean


def test_modularity_rule_pack_descriptor_and_catalog_are_stable() -> None:
    descriptor = PythonModularityRulePack().descriptor()
    rules = python_modularity_rules()

    assert descriptor.id == "python.modularity"
    assert descriptor.to_dict()["domains"] == ["modularity", "architecture", "python"]
    assert [rule.rule_id for rule in rules] == ["PY-MOD-R006", "PY-MOD-R007"]


def _large_unit_test_source() -> str:
    parts = ["VALUE = 1\n"]
    for index in range(8):
        parts.append(f"def test_case_{index}() -> None:\n")
        for line in range(34):
            parts.append(f"    value_{line} = VALUE + {line}\n")
        parts.append("    assert value_0 == 1\n\n")
    return "".join(parts)


def _large_multi_responsibility_module_source() -> str:
    parts = [
        '"""Large feature module for tests."""\n\n',
        "class Planner:\n    pass\n\n",
        "class RuntimeState:\n    pass\n\n",
        "MODE = 'fast'\n",
        "DEFAULT_LIMIT = 32\n\n",
    ]
    for index in range(28):
        parts.append(f"def helper_{index}(input_value: int) -> int:\n")
        for line in range(8):
            parts.append(f"    value_{line} = input_value + {line} + DEFAULT_LIMIT\n")
        parts.append("    return value_0\n\n")
    return "".join(parts)
