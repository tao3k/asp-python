"""Python-native AST-backed source parser for modern Python projects."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_MODULE_IDENTITY_EXPORTS = frozenset(
    {
        "python_module_is_package_init",
        "python_module_name_from_path",
        "python_module_namespace_parts",
    }
)
_MODULE_POLICY_EXPORTS = frozenset(
    {
        "python_module_has_public_surface",
        "python_module_has_public_symbol_surface",
    }
)
_NAME_POLICY_EXPORTS = frozenset(
    {
        "python_name_is_public",
        "python_scope_is_public",
    }
)
_PROJECT_MODEL_EXPORTS = frozenset(
    {
        "PythonProjectDependency",
        "PythonProjectEntryPoint",
        "PythonProjectImportName",
        "PythonProjectMetadata",
        "PythonProjectScript",
        "PythonPytestOptions",
    }
)
_PYPROJECT_EXPORTS = frozenset(
    {
        "PythonPyprojectParseError",
        "parse_python_project_metadata",
        "parse_python_pyproject_document",
    }
)
_REASONING_TREE_EXPORTS = frozenset(
    {
        "PythonReasoningTreeBranch",
        "PythonReasoningTreeFacts",
        "PythonReasoningTreeImportEdge",
        "PythonReasoningTreeNode",
        "PythonReasoningTreeShadow",
        "python_reasoning_tree_facts",
    }
)
_SYMBOL_POLICY_EXPORTS = frozenset(
    {
        "python_assignment_is_public_top_level",
        "python_symbol_is_callable",
        "python_symbol_is_class",
        "python_symbol_is_public_callable",
        "python_symbol_is_public_callable_boundary",
        "python_symbol_is_public_class",
        "python_symbol_is_public_top_level",
        "python_symbol_is_test_function",
        "python_symbol_is_top_level_callable",
    }
)
_MODEL_EXPORTS = frozenset(
    {
        "PythonAssignmentTarget",
        "PythonCall",
        "PythonCallEffect",
        "PythonClassShape",
        "PythonDiagnostic",
        "PythonDiagnosticSeverity",
        "PythonExportContract",
        "PythonExportContractKind",
        "PythonFunctionControlFlow",
        "PythonImport",
        "PythonModuleReport",
        "PythonModuleShape",
        "PythonNameBinding",
        "PythonReference",
        "PythonReferenceKind",
        "PythonScope",
        "PythonSymbol",
        "PythonSymbolKind",
        "SourceLocation",
    }
)
_PARSER_EXPORTS = frozenset(
    {
        "parse_python_file",
        "parse_python_source",
    }
)

__all__ = [
    "PythonAssignmentTarget",
    "PythonClassShape",
    "PythonCall",
    "PythonCallEffect",
    "PythonDiagnostic",
    "PythonDiagnosticSeverity",
    "PythonExportContract",
    "PythonExportContractKind",
    "PythonFunctionControlFlow",
    "PythonImport",
    "PythonModuleReport",
    "PythonModuleShape",
    "PythonNameBinding",
    "PythonProjectDependency",
    "PythonProjectEntryPoint",
    "PythonProjectImportName",
    "PythonProjectMetadata",
    "PythonPyprojectParseError",
    "PythonProjectScript",
    "PythonPytestOptions",
    "PythonReference",
    "PythonReferenceKind",
    "PythonReasoningTreeBranch",
    "PythonReasoningTreeFacts",
    "PythonReasoningTreeImportEdge",
    "PythonReasoningTreeNode",
    "PythonReasoningTreeShadow",
    "PythonScope",
    "PythonSymbol",
    "PythonSymbolKind",
    "SourceLocation",
    "__version__",
    "parse_python_file",
    "parse_python_project_metadata",
    "parse_python_pyproject_document",
    "parse_python_source",
    "python_module_is_package_init",
    "python_module_has_public_surface",
    "python_module_has_public_symbol_surface",
    "python_module_name_from_path",
    "python_module_namespace_parts",
    "python_name_is_public",
    "python_scope_is_public",
    "python_reasoning_tree_facts",
    "python_assignment_is_public_top_level",
    "python_symbol_is_callable",
    "python_symbol_is_class",
    "python_symbol_is_public_callable",
    "python_symbol_is_public_callable_boundary",
    "python_symbol_is_public_class",
    "python_symbol_is_public_top_level",
    "python_symbol_is_test_function",
    "python_symbol_is_top_level_callable",
]


def __getattr__(name: str) -> Any:
    """Resolve public facade symbols lazily so CLI startup stays small."""

    if name == "__version__":
        return _load_export("._version", name)
    if name in _MODULE_IDENTITY_EXPORTS:
        return _load_export("._module_identity", name)
    if name in _MODULE_POLICY_EXPORTS:
        return _load_export("._module_policy", name)
    if name in _NAME_POLICY_EXPORTS:
        return _load_export("._name_policy", name)
    if name in _PROJECT_MODEL_EXPORTS:
        return _load_export("._project_model", name)
    if name in _PYPROJECT_EXPORTS:
        return _load_export("._pyproject_metadata", name)
    if name in _REASONING_TREE_EXPORTS:
        return _load_export("._reasoning_tree", name)
    if name in _SYMBOL_POLICY_EXPORTS:
        return _load_export("._symbol_policy", name)
    if name in _MODEL_EXPORTS:
        return _load_export(".model", name)
    if name in _PARSER_EXPORTS:
        return _load_export(".parser", name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return public lazy exports alongside initialized module globals."""

    return sorted({*globals(), *__all__})


def _load_export(module_name: str, name: str) -> Any:
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
