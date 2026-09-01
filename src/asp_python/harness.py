"""Public facade for the embedded Python language project harness."""

from __future__ import annotations

from ._agent_policy import PythonAgentPolicyRulePack
from ._agent_policy_catalog import python_agent_policy_rules
from ._agent_snapshot import (
    render_asp_python_agent_snapshot,
    render_asp_python_agent_snapshot_with_config,
)
from ._cli import run_cli, run_cli_from_env
from ._discovery import (
    asp_python_paths,
    asp_python_scope,
    discover_python_files,
)
from ._model import (
    AspPythonConfig,
    AspPythonFinding,
    AspPythonReport,
    AspPythonRule,
    PythonLangRulePack,
    PythonProjectHarnessScope,
    PythonRulePackDescriptor,
)
from ._modern_design import PythonModernDesignRulePack
from ._modern_design_catalog import python_modern_design_rules
from ._modularity import PythonModularityRulePack, python_modularity_rules
from ._project_config import read_asp_python_config
from ._project_policy import PythonProjectPolicyRulePack
from ._project_policy_catalog import python_project_policy_rules
from ._pytest import asp_python_test
from ._render import (
    render_python_lang_harness,
    render_python_lang_harness_advice,
    render_python_lang_harness_json,
    render_python_reasoning_tree,
)
from ._rule_packs import (
    default_python_harness_config,
    default_python_lang_rule_packs,
    python_rule_pack_descriptors,
)
from ._runner import (
    assert_asp_python_clean,
    assert_python_lang_harness_clean,
    run_asp_python,
    run_python_lang_harness,
)
from ._semantic_language import (
    python_semantic_language_registration,
    semantic_language_registry_document,
)
from ._semantic_search import (
    PythonSemanticSearchOptions,
    build_python_semantic_search_packet,
    render_python_semantic_search_packet,
    render_python_semantic_search_packet_json,
)
from ._syntax import PythonSyntaxRulePack
from ._syntax_catalog import python_syntax_rules
from ._test_layout import PythonTestLayoutRulePack
from ._test_layout_catalog import python_test_layout_rules
from .verification import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationEvidence,
    PythonVerificationPhase,
    PythonVerificationPlan,
    PythonVerificationPolicy,
    PythonVerificationProfileCandidate,
    PythonVerificationProfileHint,
    PythonVerificationProfileIndex,
    PythonVerificationReceipt,
    PythonVerificationReportArtifact,
    PythonVerificationReportBundle,
    PythonVerificationReportObligation,
    PythonVerificationReportPersistence,
    PythonVerificationReportWriteConfig,
    PythonVerificationReportWriteReceipt,
    PythonVerificationRequirement,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTask,
    PythonVerificationTaskContract,
    PythonVerificationTaskKind,
    PythonVerificationTaskState,
    PythonVerificationWaiver,
    build_python_verification_performance_index,
    build_python_verification_profile_index,
    build_python_verification_profile_index_with_config,
    build_python_verification_report_bundle,
    build_python_verification_task_index,
    plan_python_project_verification,
    plan_python_project_verification_with_config,
    render_python_verification_performance_index_json,
    render_python_verification_plan,
    render_python_verification_plan_json,
    render_python_verification_profile_index,
    render_python_verification_profile_index_json,
    render_python_verification_report_artifact_json,
    render_python_verification_report_bundle_json,
    render_python_verification_skill_contracts,
    render_python_verification_task_index_json,
    write_python_verification_reports,
)

__all__ = [
    "PythonAgentPolicyRulePack",
    "AspPythonConfig",
    "AspPythonFinding",
    "AspPythonReport",
    "AspPythonRule",
    "PythonLangRulePack",
    "PythonModernDesignRulePack",
    "PythonModularityRulePack",
    "PythonProjectHarnessScope",
    "PythonProjectPolicyRulePack",
    "PythonRulePackDescriptor",
    "PythonSemanticSearchOptions",
    "PythonSyntaxRulePack",
    "PythonTestLayoutRulePack",
    "PythonOwnerResponsibility",
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
    "assert_python_lang_harness_clean",
    "assert_asp_python_clean",
    "build_python_semantic_search_packet",
    "default_python_harness_config",
    "default_python_lang_rule_packs",
    "discover_python_files",
    "python_agent_policy_rules",
    "python_modern_design_rules",
    "python_modularity_rules",
    "asp_python_paths",
    "asp_python_scope",
    "asp_python_test",
    "python_project_policy_rules",
    "read_asp_python_config",
    "python_semantic_language_registration",
    "python_rule_pack_descriptors",
    "python_syntax_rules",
    "python_test_layout_rules",
    "build_python_verification_performance_index",
    "build_python_verification_profile_index",
    "build_python_verification_profile_index_with_config",
    "build_python_verification_report_bundle",
    "build_python_verification_task_index",
    "plan_python_project_verification",
    "plan_python_project_verification_with_config",
    "render_python_lang_harness",
    "render_python_lang_harness_advice",
    "render_python_lang_harness_json",
    "render_python_reasoning_tree",
    "render_asp_python_agent_snapshot",
    "render_asp_python_agent_snapshot_with_config",
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
    "write_python_verification_reports",
    "run_cli",
    "run_cli_from_env",
    "run_python_lang_harness",
    "run_asp_python",
    "semantic_language_registry_document",
]
