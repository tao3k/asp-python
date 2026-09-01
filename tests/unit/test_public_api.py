from __future__ import annotations

import asp_python as harness_api
import asp_python.harness as harness_facade
import python_lang_parser as parser_api


def test_root_package_reexports_parser_fact_models() -> None:
    assert harness_api.PythonCallEffect is parser_api.PythonCallEffect
    assert harness_api.PythonClassShape is parser_api.PythonClassShape
    assert harness_api.PythonExportContract is parser_api.PythonExportContract
    assert harness_api.PythonExportContractKind is parser_api.PythonExportContractKind
    assert harness_api.PythonFunctionControlFlow is parser_api.PythonFunctionControlFlow
    assert harness_api.PythonModuleShape is parser_api.PythonModuleShape
    assert harness_api.PythonProjectDependency is parser_api.PythonProjectDependency
    assert harness_api.PythonProjectEntryPoint is parser_api.PythonProjectEntryPoint
    assert harness_api.PythonProjectImportName is parser_api.PythonProjectImportName
    assert harness_api.PythonProjectMetadata is parser_api.PythonProjectMetadata
    assert harness_api.PythonProjectScript is parser_api.PythonProjectScript
    assert harness_api.PythonPytestOptions is parser_api.PythonPytestOptions
    assert harness_api.PythonReasoningTreeFacts is parser_api.PythonReasoningTreeFacts
    assert (
        harness_api.PythonReasoningTreeImportEdge
        is parser_api.PythonReasoningTreeImportEdge
    )
    assert harness_api.PythonReasoningTreeNode is parser_api.PythonReasoningTreeNode
    assert (
        harness_api.python_reasoning_tree_facts
        is parser_api.python_reasoning_tree_facts
    )
    assert (
        harness_api.parse_python_project_metadata
        is parser_api.parse_python_project_metadata
    )
    assert (
        harness_api.python_module_namespace_parts
        is parser_api.python_module_namespace_parts
    )
    assert (
        harness_api.python_module_name_from_path
        is parser_api.python_module_name_from_path
    )
    assert (
        harness_api.python_module_is_package_init
        is parser_api.python_module_is_package_init
    )
    assert harness_api.python_name_is_public is parser_api.python_name_is_public
    assert harness_api.python_scope_is_public is parser_api.python_scope_is_public
    assert (
        harness_api.python_assignment_is_public_top_level
        is parser_api.python_assignment_is_public_top_level
    )
    assert (
        harness_api.python_module_has_public_surface
        is parser_api.python_module_has_public_surface
    )
    assert (
        harness_api.python_module_has_public_symbol_surface
        is parser_api.python_module_has_public_symbol_surface
    )
    assert harness_api.python_symbol_is_callable is parser_api.python_symbol_is_callable
    assert harness_api.python_symbol_is_class is parser_api.python_symbol_is_class
    assert (
        harness_api.python_symbol_is_public_callable
        is parser_api.python_symbol_is_public_callable
    )
    assert (
        harness_api.python_symbol_is_public_callable_boundary
        is parser_api.python_symbol_is_public_callable_boundary
    )
    assert (
        harness_api.python_symbol_is_public_class
        is parser_api.python_symbol_is_public_class
    )
    assert (
        harness_api.python_symbol_is_public_top_level
        is parser_api.python_symbol_is_public_top_level
    )
    assert (
        harness_api.python_symbol_is_top_level_callable
        is parser_api.python_symbol_is_top_level_callable
    )
    assert (
        harness_api.python_symbol_is_test_function
        is parser_api.python_symbol_is_test_function
    )
    assert "python_module_namespace_parts" in harness_api.__all__
    assert "python_module_name_from_path" in harness_api.__all__
    assert "python_module_is_package_init" in harness_api.__all__
    assert "python_name_is_public" in harness_api.__all__
    assert "PythonReasoningTreeFacts" in harness_api.__all__
    assert "PythonProjectMetadata" in harness_api.__all__
    assert "PythonProjectDependency" in harness_api.__all__
    assert "PythonPytestOptions" in harness_api.__all__
    assert "parse_python_project_metadata" in harness_api.__all__
    assert "PythonReasoningTreeImportEdge" in harness_api.__all__
    assert "PythonReasoningTreeNode" in harness_api.__all__
    assert "PythonProjectMetadata" in parser_api.__all__
    assert "PythonClassShape" in parser_api.__all__
    assert "PythonClassShape" in harness_api.__all__
    assert "PythonProjectDependency" in parser_api.__all__
    assert "PythonPytestOptions" in parser_api.__all__
    assert "PythonReasoningTreeImportEdge" in parser_api.__all__
    assert "PythonFunctionControlFlow" in parser_api.__all__
    assert "PythonFunctionControlFlow" in harness_api.__all__
    assert "parse_python_project_metadata" in parser_api.__all__
    assert "python_reasoning_tree_facts" in harness_api.__all__
    assert "python_scope_is_public" in harness_api.__all__
    assert "python_assignment_is_public_top_level" in harness_api.__all__
    assert "python_module_has_public_surface" in harness_api.__all__
    assert "python_module_has_public_symbol_surface" in harness_api.__all__
    assert "python_symbol_is_callable" in harness_api.__all__
    assert "python_symbol_is_class" in harness_api.__all__
    assert "python_symbol_is_public_callable" in harness_api.__all__
    assert "python_symbol_is_public_callable_boundary" in harness_api.__all__
    assert "python_symbol_is_public_class" in harness_api.__all__
    assert "python_symbol_is_public_top_level" in harness_api.__all__
    assert "python_symbol_is_top_level_callable" in harness_api.__all__
    assert "python_symbol_is_test_function" in harness_api.__all__


def test_root_package_reexports_embedding_harness_surface() -> None:
    assert harness_api.AspPythonConfig is harness_facade.AspPythonConfig
    assert harness_api.AspPythonReport is harness_facade.AspPythonReport
    assert (
        harness_api.PythonVerificationPolicy is harness_facade.PythonVerificationPolicy
    )
    assert (
        harness_api.PythonVerificationProfileHint
        is harness_facade.PythonVerificationProfileHint
    )
    assert (
        harness_api.PythonVerificationTaskKind
        is harness_facade.PythonVerificationTaskKind
    )
    assert (
        harness_api.PythonProjectPolicyRulePack
        is harness_facade.PythonProjectPolicyRulePack
    )
    assert (
        harness_api.default_python_harness_config
        is harness_facade.default_python_harness_config
    )
    assert harness_api.asp_python_test is harness_facade.asp_python_test
    assert (
        harness_api.python_project_policy_rules
        is harness_facade.python_project_policy_rules
    )
    assert (
        harness_api.render_python_lang_harness
        is harness_facade.render_python_lang_harness
    )
    assert (
        harness_api.render_python_lang_harness_advice
        is harness_facade.render_python_lang_harness_advice
    )
    assert (
        harness_api.render_python_lang_harness_json
        is harness_facade.render_python_lang_harness_json
    )
    assert (
        harness_api.render_python_reasoning_tree
        is harness_facade.render_python_reasoning_tree
    )
    assert (
        harness_api.render_asp_python_agent_snapshot
        is harness_facade.render_asp_python_agent_snapshot
    )
    assert (
        harness_api.render_asp_python_agent_snapshot_with_config
        is harness_facade.render_asp_python_agent_snapshot_with_config
    )
    assert harness_api.read_asp_python_config is harness_facade.read_asp_python_config
    assert (
        harness_api.python_rule_pack_descriptors
        is harness_facade.python_rule_pack_descriptors
    )
    assert harness_api.python_syntax_rules is harness_facade.python_syntax_rules
    assert harness_api.run_cli is harness_facade.run_cli
    assert harness_api.run_cli_from_env is harness_facade.run_cli_from_env
    assert (
        harness_api.plan_python_project_verification
        is harness_facade.plan_python_project_verification
    )
    assert (
        harness_api.render_python_verification_plan
        is harness_facade.render_python_verification_plan
    )
    assert "render_python_lang_harness_advice" in harness_api.__all__
    assert "render_python_lang_harness_json" in harness_api.__all__
    assert "render_asp_python_agent_snapshot" in harness_api.__all__
    assert "render_asp_python_agent_snapshot_with_config" in harness_api.__all__
    assert "render_python_reasoning_tree" in harness_api.__all__
    assert "read_asp_python_config" in harness_api.__all__
    assert "run_cli_from_env" in harness_api.__all__
    assert "python_syntax_rules" in harness_api.__all__
    assert "PythonVerificationPolicy" in harness_api.__all__
    assert "PythonVerificationProfileHint" in harness_api.__all__
    assert "PythonVerificationTaskKind" in harness_api.__all__
    assert "plan_python_project_verification" in harness_api.__all__
    assert "render_python_verification_plan" in harness_api.__all__
