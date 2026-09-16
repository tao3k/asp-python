"""Default rule-pack configuration for ASP Python runs."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from ._agent_policy import PythonAgentPolicyRulePack
from ._model import AspPythonConfig, AspPythonRulePack, PythonRulePackDescriptor
from ._modern_design import PythonModernDesignRulePack
from ._modularity import PythonModularityRulePack
from ._project_config import (
    apply_asp_project_discovery_config,
    read_asp_python_config,
)
from ._project_policy import PythonProjectPolicyRulePack
from ._syntax import PythonSyntaxRulePack
from ._test_layout import PythonTestLayoutRulePack

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def default_asp_python_rule_packs() -> tuple[AspPythonRulePack, ...]:
    """Return the default deterministic Python language rule packs."""

    return (
        PythonSyntaxRulePack(),
        PythonProjectPolicyRulePack(),
        PythonModernDesignRulePack(),
        PythonModularityRulePack(),
        PythonTestLayoutRulePack(),
        PythonAgentPolicyRulePack(),
    )


def python_rule_pack_descriptors() -> tuple[PythonRulePackDescriptor, ...]:
    """Return stable metadata for default ASP Python rule packs."""

    return tuple(
        rule_pack.descriptor() for rule_pack in default_asp_python_rule_packs()
    )


def default_asp_python_config() -> AspPythonConfig:
    """Return the default ASP Python configuration."""

    return AspPythonConfig(rule_packs=default_asp_python_rule_packs())


def resolve_asp_python_config(
    config: AspPythonConfig | None,
    *,
    rule_packs: Sequence[AspPythonRulePack] | None,
) -> AspPythonConfig:
    """Resolve caller config and one-shot rule-pack overrides."""

    selected_config = default_asp_python_config() if config is None else config
    if rule_packs is None:
        return selected_config
    return replace(selected_config, rule_packs=tuple(rule_packs))


def resolve_asp_python_project_config(
    project_root: str | Path,
    config: AspPythonConfig | None,
    *,
    rule_packs: Sequence[AspPythonRulePack] | None,
) -> AspPythonConfig:
    """Resolve config for project-root runs, including pyproject policy."""

    selected_config = read_asp_python_config(project_root) if config is None else config
    resolved = resolve_asp_python_config(selected_config, rule_packs=rule_packs)
    return apply_asp_project_discovery_config(project_root, resolved)


def selected_rule_packs(
    config: AspPythonConfig,
) -> tuple[AspPythonRulePack, ...]:
    """Return configured rule packs, falling back to the default catalog."""

    if config.rule_packs is not None:
        return config.rule_packs
    return default_asp_python_rule_packs()
