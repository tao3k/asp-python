from __future__ import annotations

import asp_python as asp_python_api
import asp_python.api as asp_python_facade
import python_lang_parser as parser_api


def test_root_package_reexports_parser_fact_models() -> None:
    assert asp_python_api.PythonCallEffect is parser_api.PythonCallEffect
    assert asp_python_api.PythonClassShape is parser_api.PythonClassShape
    assert asp_python_api.PythonExportContract is parser_api.PythonExportContract
    assert (
        asp_python_api.PythonExportContractKind is parser_api.PythonExportContractKind
    )
    assert (
        asp_python_api.PythonFunctionControlFlow is parser_api.PythonFunctionControlFlow
    )
    assert asp_python_api.PythonModuleShape is parser_api.PythonModuleShape
    assert asp_python_api.PythonProjectDependency is parser_api.PythonProjectDependency
    assert asp_python_api.PythonProjectEntryPoint is parser_api.PythonProjectEntryPoint
    assert asp_python_api.PythonProjectImportName is parser_api.PythonProjectImportName
    assert asp_python_api.PythonProjectMetadata is parser_api.PythonProjectMetadata
    assert asp_python_api.PythonProjectScript is parser_api.PythonProjectScript
    assert asp_python_api.PythonPytestOptions is parser_api.PythonPytestOptions
    assert (
        asp_python_api.PythonReasoningTreeFacts is parser_api.PythonReasoningTreeFacts
    )
    assert (
        asp_python_api.PythonReasoningTreeImportEdge
        is parser_api.PythonReasoningTreeImportEdge
    )
    assert asp_python_api.PythonReasoningTreeNode is parser_api.PythonReasoningTreeNode
    assert (
        asp_python_api.python_reasoning_tree_facts
        is parser_api.python_reasoning_tree_facts
    )
    assert (
        asp_python_api.parse_python_project_metadata
        is parser_api.parse_python_project_metadata
    )
    assert (
        asp_python_api.python_module_namespace_parts
        is parser_api.python_module_namespace_parts
    )
    assert (
        asp_python_api.python_module_name_from_path
        is parser_api.python_module_name_from_path
    )
    assert (
        asp_python_api.python_module_is_package_init
        is parser_api.python_module_is_package_init
    )
    assert asp_python_api.python_name_is_public is parser_api.python_name_is_public
    assert asp_python_api.python_scope_is_public is parser_api.python_scope_is_public
    assert (
        asp_python_api.python_assignment_is_public_top_level
        is parser_api.python_assignment_is_public_top_level
    )
    assert (
        asp_python_api.python_module_has_public_surface
        is parser_api.python_module_has_public_surface
    )
    assert (
        asp_python_api.python_module_has_public_symbol_surface
        is parser_api.python_module_has_public_symbol_surface
    )
    assert (
        asp_python_api.python_symbol_is_callable is parser_api.python_symbol_is_callable
    )
    assert asp_python_api.python_symbol_is_class is parser_api.python_symbol_is_class
    assert (
        asp_python_api.python_symbol_is_public_callable
        is parser_api.python_symbol_is_public_callable
    )
    assert (
        asp_python_api.python_symbol_is_public_callable_boundary
        is parser_api.python_symbol_is_public_callable_boundary
    )
    assert (
        asp_python_api.python_symbol_is_public_class
        is parser_api.python_symbol_is_public_class
    )
    assert (
        asp_python_api.python_symbol_is_public_top_level
        is parser_api.python_symbol_is_public_top_level
    )
    assert (
        asp_python_api.python_symbol_is_top_level_callable
        is parser_api.python_symbol_is_top_level_callable
    )
    assert (
        asp_python_api.python_symbol_is_test_function
        is parser_api.python_symbol_is_test_function
    )
    assert "python_module_namespace_parts" in asp_python_api.__all__
    assert "python_module_name_from_path" in asp_python_api.__all__
    assert "python_module_is_package_init" in asp_python_api.__all__
    assert "python_name_is_public" in asp_python_api.__all__
    assert "PythonReasoningTreeFacts" in asp_python_api.__all__
    assert "PythonProjectMetadata" in asp_python_api.__all__
    assert "PythonProjectDependency" in asp_python_api.__all__
    assert "PythonPytestOptions" in asp_python_api.__all__
    assert "parse_python_project_metadata" in asp_python_api.__all__
    assert "PythonReasoningTreeImportEdge" in asp_python_api.__all__
    assert "PythonReasoningTreeNode" in asp_python_api.__all__
    assert "PythonProjectMetadata" in parser_api.__all__
    assert "PythonClassShape" in parser_api.__all__
    assert "PythonClassShape" in asp_python_api.__all__
    assert "PythonProjectDependency" in parser_api.__all__
    assert "PythonPytestOptions" in parser_api.__all__
    assert "PythonReasoningTreeImportEdge" in parser_api.__all__
    assert "PythonFunctionControlFlow" in parser_api.__all__
    assert "PythonFunctionControlFlow" in asp_python_api.__all__
    assert "parse_python_project_metadata" in parser_api.__all__
    assert "python_reasoning_tree_facts" in asp_python_api.__all__
    assert "python_scope_is_public" in asp_python_api.__all__
    assert "python_assignment_is_public_top_level" in asp_python_api.__all__
    assert "python_module_has_public_surface" in asp_python_api.__all__
    assert "python_module_has_public_symbol_surface" in asp_python_api.__all__
    assert "python_symbol_is_callable" in asp_python_api.__all__
    assert "python_symbol_is_class" in asp_python_api.__all__
    assert "python_symbol_is_public_callable" in asp_python_api.__all__
    assert "python_symbol_is_public_callable_boundary" in asp_python_api.__all__
    assert "python_symbol_is_public_class" in asp_python_api.__all__
    assert "python_symbol_is_public_top_level" in asp_python_api.__all__
    assert "python_symbol_is_top_level_callable" in asp_python_api.__all__
    assert "python_symbol_is_test_function" in asp_python_api.__all__


def test_root_package_reexports_asp_python_surface() -> None:
    assert asp_python_api.AspPythonConfig is asp_python_facade.AspPythonConfig
    assert asp_python_api.AspPythonReport is asp_python_facade.AspPythonReport
    assert (
        asp_python_api.PythonVerificationPolicy
        is asp_python_facade.PythonVerificationPolicy
    )
    assert (
        asp_python_api.PythonVerificationProfileHint
        is asp_python_facade.PythonVerificationProfileHint
    )
    assert (
        asp_python_api.PythonVerificationTaskKind
        is asp_python_facade.PythonVerificationTaskKind
    )
    assert (
        asp_python_api.PythonProjectPolicyRulePack
        is asp_python_facade.PythonProjectPolicyRulePack
    )
    assert (
        asp_python_api.default_asp_python_config
        is asp_python_facade.default_asp_python_config
    )
    assert asp_python_api.asp_python_test is asp_python_facade.asp_python_test
    assert (
        asp_python_api.python_project_policy_rules
        is asp_python_facade.python_project_policy_rules
    )
    assert (
        asp_python_api.render_asp_python_report
        is asp_python_facade.render_asp_python_report
    )
    assert (
        asp_python_api.render_asp_python_report_advice
        is asp_python_facade.render_asp_python_report_advice
    )
    assert (
        asp_python_api.render_asp_python_report_json
        is asp_python_facade.render_asp_python_report_json
    )
    assert (
        asp_python_api.render_python_reasoning_tree
        is asp_python_facade.render_python_reasoning_tree
    )
    assert (
        asp_python_api.render_asp_python_agent_snapshot
        is asp_python_facade.render_asp_python_agent_snapshot
    )
    assert (
        asp_python_api.render_asp_python_agent_snapshot_with_config
        is asp_python_facade.render_asp_python_agent_snapshot_with_config
    )
    assert (
        asp_python_api.read_asp_python_config
        is asp_python_facade.read_asp_python_config
    )
    assert (
        asp_python_api.python_rule_pack_descriptors
        is asp_python_facade.python_rule_pack_descriptors
    )
    assert asp_python_api.python_syntax_rules is asp_python_facade.python_syntax_rules
    assert asp_python_api.run_cli is asp_python_facade.run_cli
    assert asp_python_api.run_cli_from_env is asp_python_facade.run_cli_from_env
    assert (
        asp_python_api.plan_python_project_verification
        is asp_python_facade.plan_python_project_verification
    )
    assert (
        asp_python_api.render_python_verification_plan
        is asp_python_facade.render_python_verification_plan
    )
    assert "render_asp_python_report_advice" in asp_python_api.__all__
    assert "render_asp_python_report_json" in asp_python_api.__all__
    assert "render_asp_python_agent_snapshot" in asp_python_api.__all__
    assert "render_asp_python_agent_snapshot_with_config" in asp_python_api.__all__
    assert "render_python_reasoning_tree" in asp_python_api.__all__
    assert "read_asp_python_config" in asp_python_api.__all__
    assert "run_cli_from_env" in asp_python_api.__all__
    assert "python_syntax_rules" in asp_python_api.__all__
    assert "PythonVerificationPolicy" in asp_python_api.__all__
    assert "PythonVerificationProfileHint" in asp_python_api.__all__
    assert "PythonVerificationTaskKind" in asp_python_api.__all__
    assert "plan_python_project_verification" in asp_python_api.__all__
    assert "render_python_verification_plan" in asp_python_api.__all__
