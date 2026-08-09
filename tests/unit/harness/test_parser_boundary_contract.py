from __future__ import annotations

from pathlib import Path

_PROJECT_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").exists() and (parent / "src").exists()
)


def test_harness_policy_does_not_parse_python_source_directly() -> None:
    harness_sources = sorted(
        (_PROJECT_ROOT / "src" / "python_lang_project_harness").glob("*_policy*.py")
    )

    for path in harness_sources:
        source = path.read_text(encoding="utf-8")
        assert "import ast" not in source, path
        assert "import tokenize" not in source, path
        assert "ast.parse" not in source, path
        assert "tokenize." not in source, path


def test_harness_semantic_roles_use_parser_symbol_helpers() -> None:
    harness_sources = sorted(
        (_PROJECT_ROOT / "src" / "python_lang_project_harness").rglob("*.py")
    )
    for path in harness_sources:
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert "PythonSymbolKind" not in source, path

    test_bloat = (
        _PROJECT_ROOT / "src" / "python_lang_project_harness" / "_test_layout_bloat.py"
    ).read_text(encoding="utf-8")
    agent_policy = (
        _PROJECT_ROOT / "src" / "python_lang_project_harness" / "_agent_policy.py"
    ).read_text(encoding="utf-8")
    typed_policy = (
        _PROJECT_ROOT
        / "src"
        / "python_lang_project_harness"
        / "_project_policy_typed.py"
    ).read_text(encoding="utf-8")
    namespace_index = (
        _PROJECT_ROOT
        / "src"
        / "python_lang_project_harness"
        / "_agent_namespace_index.py"
    ).read_text(encoding="utf-8")

    assert "python_symbol_is_test_function(" in test_bloat
    assert 'symbol.name.startswith("test_")' not in test_bloat
    assert "python_symbol_is_public_callable(" in agent_policy
    assert "python_module_has_public_symbol_surface(" in agent_policy
    assert "python_symbol_is_public_class(" in typed_policy
    assert "python_symbol_is_public_callable_boundary(" in typed_policy
    assert "python_module_has_public_surface(" in typed_policy
    assert "symbol.is_public" not in typed_policy
    assert "python_symbol_is_callable(" in namespace_index
    assert "python_symbol_is_class(" in namespace_index
    assert "python_symbol_is_public_top_level(" in namespace_index
    assert "python_assignment_is_public_top_level(" in namespace_index
    assert "symbol.is_top_level" not in namespace_index
    assert "symbol.is_public" not in namespace_index
    assert "assignment.is_top_level" not in namespace_index
    assert "assignment.is_public" not in namespace_index


def test_agent_namespace_policy_uses_parser_module_identity_helpers() -> None:
    source = (
        _PROJECT_ROOT / "src" / "python_lang_project_harness" / "_agent_namespace.py"
    ).read_text(encoding="utf-8")

    assert "python_module_namespace_parts(" in source
    assert "relative_to(" not in source
    assert "with_suffix(" not in source


def test_python_semantic_policy_uses_parser_name_helpers() -> None:
    typed_policy = (
        _PROJECT_ROOT
        / "src"
        / "python_lang_project_harness"
        / "_project_policy_typed.py"
    ).read_text(encoding="utf-8")
    modern_design = (
        _PROJECT_ROOT / "src" / "python_lang_project_harness" / "_modern_design.py"
    ).read_text(encoding="utf-8")

    assert "python_symbol_is_public_class(" in typed_policy
    assert "_name_is_public" not in typed_policy
    assert "python_module_is_package_init(" in modern_design
    assert 'name != "__init__.py"' not in modern_design


def test_test_layout_python_source_lines_use_parser_reports() -> None:
    layout = (
        _PROJECT_ROOT / "src" / "python_lang_project_harness" / "_test_layout.py"
    ).read_text(encoding="utf-8")
    entries = (
        _PROJECT_ROOT
        / "src"
        / "python_lang_project_harness"
        / "_test_layout_entries.py"
    ).read_text(encoding="utf-8")

    assert "tests_root_entry_findings(tests_dir, pack_id, modules)" in layout
    assert 'if path.suffix == ".py":' in entries
    assert "return report.source_line(line)" in entries


def test_harness_pyproject_metadata_comes_from_parser_boundary() -> None:
    harness_sources = sorted(
        (_PROJECT_ROOT / "src" / "python_lang_project_harness").rglob("*.py")
    )

    for path in harness_sources:
        if path.name in {
            "_project_config.py",
            "_project_resolution_candidates.py",
            "_test_layout_config.py",
        }:
            continue
        source = path.read_text(encoding="utf-8")
        assert "import tomllib" not in source, path
        assert "tomllib." not in source, path


def test_agent_readability_policy_consumes_parser_function_facts() -> None:
    readability_root = (
        _PROJECT_ROOT / "src" / "python_lang_project_harness" / "agent_readability"
    )

    for path in sorted(readability_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "import ast" not in source, path
        assert "ast." not in source, path
        assert "symbol.is_top_level" not in source, path
        assert "symbol.is_public" not in source, path

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(readability_root.glob("*.py"))
    )
    assert "symbol.control_flow" in combined
    assert "symbol.class_shape" in combined
    assert "PythonFunctionControlFlow" in combined
    assert "python_symbol_is_public_callable(" in combined
