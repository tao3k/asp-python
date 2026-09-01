"""Project-level Python language harness helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

DISTRIBUTION_NAME = "asp-python"

_CLI_EXPORTS = frozenset({"run_cli", "run_cli_from_env"})
_HARNESS_RULES_EXPORTS = frozenset(
    {
        "python_harness_rules_markdown",
        "render_python_harness_rules_markdown",
        "write_python_harness_rules_to_unit_tests",
    }
)

_PARSER_EXPORTS = frozenset(
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
        "PythonProjectDependency",
        "PythonProjectEntryPoint",
        "PythonProjectImportName",
        "PythonProjectMetadata",
        "PythonProjectScript",
        "PythonPytestOptions",
        "PythonReasoningTreeBranch",
        "PythonReasoningTreeFacts",
        "PythonReasoningTreeImportEdge",
        "PythonReasoningTreeNode",
        "PythonReasoningTreeShadow",
        "PythonReference",
        "PythonReferenceKind",
        "PythonScope",
        "PythonSymbol",
        "PythonSymbolKind",
        "SourceLocation",
        "parse_python_file",
        "parse_python_project_metadata",
        "parse_python_source",
        "python_assignment_is_public_top_level",
        "python_module_has_public_surface",
        "python_module_has_public_symbol_surface",
        "python_module_is_package_init",
        "python_module_name_from_path",
        "python_module_namespace_parts",
        "python_name_is_public",
        "python_reasoning_tree_facts",
        "python_scope_is_public",
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

__all__ = [
    "DISTRIBUTION_NAME",
    "PythonAgentPolicyRulePack",
    "PythonAssignmentTarget",
    "PythonClassShape",
    "PythonCall",
    "PythonCallEffect",
    "PythonDiagnostic",
    "PythonDiagnosticSeverity",
    "PythonExportContract",
    "PythonExportContractKind",
    "PythonFunctionControlFlow",
    "AspPythonConfig",
    "AspPythonFinding",
    "AspPythonReport",
    "AspPythonRule",
    "PythonImport",
    "PythonLangRulePack",
    "PythonModernDesignRulePack",
    "PythonModularityRulePack",
    "PythonModuleReport",
    "PythonModuleShape",
    "PythonNameBinding",
    "PythonOwnerResponsibility",
    "PythonProjectDependency",
    "PythonProjectEntryPoint",
    "PythonProjectHarnessScope",
    "PythonProjectImportName",
    "PythonProjectMetadata",
    "PythonProjectPolicyRulePack",
    "PythonProjectScript",
    "PythonPytestOptions",
    "PythonReference",
    "PythonReferenceKind",
    "PythonReasoningTreeBranch",
    "PythonReasoningTreeFacts",
    "PythonReasoningTreeImportEdge",
    "PythonReasoningTreeNode",
    "PythonReasoningTreeShadow",
    "PythonRulePackDescriptor",
    "PythonScope",
    "PythonSemanticSearchOptions",
    "PythonSymbol",
    "PythonSymbolKind",
    "PythonSyntaxRulePack",
    "PythonTestLayoutRulePack",
    "PythonVerificationDependencySignal",
    "PythonVerificationEvidence",
    "PythonVerificationPhase",
    "PythonVerificationPlan",
    "PythonVerificationPolicy",
    "PythonVerificationProfileCandidate",
    "PythonVerificationProfileHint",
    "PythonVerificationProfileIndex",
    "PythonVerificationReceipt",
    "PythonVerificationReportArtifact",
    "PythonVerificationReportBundle",
    "PythonVerificationReportObligation",
    "PythonVerificationReportPersistence",
    "PythonVerificationReportWriteConfig",
    "PythonVerificationReportWriteReceipt",
    "PythonVerificationRequirement",
    "PythonVerificationSkillBinding",
    "PythonVerificationSkillDescriptor",
    "PythonVerificationTask",
    "PythonVerificationTaskContract",
    "PythonVerificationTaskKind",
    "PythonVerificationTaskState",
    "PythonVerificationWaiver",
    "SourceLocation",
    "__version__",
    "assert_python_lang_harness_clean",
    "assert_asp_python_clean",
    "build_python_semantic_search_packet",
    "default_python_harness_config",
    "default_python_lang_rule_packs",
    "discover_python_files",
    "build_python_verification_performance_index",
    "build_python_verification_profile_index",
    "build_python_verification_profile_index_with_config",
    "build_python_verification_report_bundle",
    "build_python_verification_task_index",
    "plan_python_project_verification",
    "plan_python_project_verification_with_config",
    "parse_python_file",
    "parse_python_project_metadata",
    "parse_python_source",
    "python_assignment_is_public_top_level",
    "python_module_has_public_surface",
    "python_module_has_public_symbol_surface",
    "python_module_is_package_init",
    "python_module_name_from_path",
    "python_module_namespace_parts",
    "python_name_is_public",
    "python_reasoning_tree_facts",
    "python_scope_is_public",
    "python_symbol_is_callable",
    "python_symbol_is_class",
    "python_symbol_is_public_callable",
    "python_symbol_is_public_callable_boundary",
    "python_symbol_is_public_class",
    "python_symbol_is_public_top_level",
    "python_symbol_is_test_function",
    "python_symbol_is_top_level_callable",
    "python_agent_policy_rules",
    "python_harness_rules_markdown",
    "python_modern_design_rules",
    "python_modularity_rules",
    "asp_python_paths",
    "asp_python_scope",
    "asp_python_test",
    "python_project_policy_rules",
    "python_rule_pack_descriptors",
    "python_semantic_language_registration",
    "python_syntax_rules",
    "python_test_layout_rules",
    "read_asp_python_config",
    "render_python_lang_harness",
    "render_python_lang_harness_advice",
    "render_python_lang_harness_json",
    "render_python_harness_rules_markdown",
    "render_asp_python_agent_snapshot",
    "render_asp_python_agent_snapshot_with_config",
    "render_python_reasoning_tree",
    "render_python_semantic_search_packet",
    "render_python_semantic_search_packet_json",
    "render_python_verification_performance_index_json",
    "render_python_verification_plan",
    "render_python_verification_plan_json",
    "render_python_verification_profile_index",
    "render_python_verification_profile_index_json",
    "render_python_verification_report_artifact_json",
    "render_python_verification_report_bundle_json",
    "render_python_verification_skill_contracts",
    "render_python_verification_task_index_json",
    "run_cli",
    "run_cli_from_env",
    "run_python_lang_harness",
    "run_asp_python",
    "semantic_language_registry_document",
    "write_python_harness_rules_to_unit_tests",
    "write_python_verification_reports",
]


def __getattr__(name: str) -> Any:
    """Resolve public facade symbols lazily so CLI startup stays small."""

    if name == "__version__":
        return _load_export("._version", name)
    if name in _CLI_EXPORTS:
        return _load_export("._cli", name)
    if name in _HARNESS_RULES_EXPORTS:
        return _load_export("._harness_rules", name)
    if name in _PARSER_EXPORTS:
        return _load_export("python_lang_parser", name)
    if name in __all__:
        return _load_export(".harness", name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return public lazy exports alongside initialized module globals."""

    return sorted({*globals(), *__all__})


def _load_export(module_name: str, name: str) -> Any:
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
