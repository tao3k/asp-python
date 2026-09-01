"""Project-local pyproject configuration for Python harness policy."""

from __future__ import annotations

import tomllib
from dataclasses import replace
from pathlib import Path
from typing import Any

from python_lang_parser._diagnostic_model import PythonDiagnosticSeverity

from ._model import AspPythonConfig
from .verification import (
    PythonOwnerResponsibility,
    PythonVerificationDependencySignal,
    PythonVerificationPhase,
    PythonVerificationPolicy,
    PythonVerificationProfileHint,
    PythonVerificationReceipt,
    PythonVerificationRequirement,
    PythonVerificationSkillBinding,
    PythonVerificationSkillDescriptor,
    PythonVerificationTaskContract,
    PythonVerificationTaskKind,
    PythonVerificationWaiver,
)

_TOOL_TABLE_NAME = "asp-python"


def read_asp_python_config(
    project_root: str | Path,
) -> AspPythonConfig | None:
    """Read `[tool.asp-python]` from `pyproject.toml`."""

    table = _read_project_config_table(Path(project_root) / "pyproject.toml")
    if not table:
        return None
    return AspPythonConfig(**_harness_config_kwargs(table))


def read_pyproject_payload(pyproject_path: Path) -> dict[str, Any]:
    """Read a project `pyproject.toml` payload at the parser boundary."""

    if not pyproject_path.exists():
        return {}
    try:
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def apply_asp_project_discovery_config(
    project_root: str | Path,
    config: AspPythonConfig,
) -> AspPythonConfig:
    """Merge nearest `asp.toml` discovery settings into a harness config."""

    table = _read_asp_discovery_table(Path(project_root))
    if not table:
        return config
    ignored = _optional_string_frozenset(table, "ignoredDirNames")
    included_hidden = _optional_string_frozenset(table, "includeHiddenDirNames")
    return replace(
        config,
        ignored_dir_names=frozenset((*config.ignored_dir_names, *ignored)),
        include_hidden_dir_names=frozenset(
            (*config.include_hidden_dir_names, *included_hidden)
        ),
    )


def _read_project_config_table(pyproject_path: Path) -> dict[str, Any] | None:
    payload = read_pyproject_payload(pyproject_path)
    if not payload:
        return None

    table = _table(_table(payload.get("tool")).get(_TOOL_TABLE_NAME))
    if not table:
        return None
    return table


def _harness_config_kwargs(table: dict[str, Any]) -> dict[str, object]:
    kwargs: dict[str, object] = {}
    _put_bool(kwargs, table, "include_tests")
    _put_string_tuple(kwargs, table, "source_dir_names")
    _put_string_tuple(kwargs, table, "test_dir_names")
    _put_string_tuple(kwargs, table, "extra_path_names")
    _put_string_frozenset(kwargs, table, "ignored_dir_names")
    _put_string_frozenset(kwargs, table, "include_hidden_dir_names")
    _put_string_frozenset(kwargs, table, "disabled_rule_ids")
    _put_string_frozenset(kwargs, table, "blocking_rule_ids")
    _put_severity_frozenset(kwargs, table, "blocking_severities")
    _put_verification_policy(kwargs, table)
    return kwargs


def _read_asp_discovery_table(project_root: Path) -> dict[str, Any] | None:
    config_path = _nearest_asp_toml(project_root)
    if config_path is None:
        return None
    try:
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return None
    table = _table(payload.get("discovery"))
    return table or None


def _nearest_asp_toml(project_root: Path) -> Path | None:
    for candidate_root in (project_root, *project_root.parents):
        candidate = candidate_root / "asp.toml"
        if candidate.is_file():
            return candidate
    return None


def _optional_string_frozenset(
    table: dict[str, Any],
    key: str,
) -> frozenset[str]:
    value = table.get(key)
    if value is None:
        return frozenset()
    return frozenset(_string_tuple(value, key=key))


def _put_bool(
    kwargs: dict[str, object],
    table: dict[str, Any],
    key: str,
) -> None:
    value = table.get(key)
    if value is None:
        return
    if not isinstance(value, bool):
        raise ValueError(f"{_TOOL_TABLE_NAME}.{key} must be a boolean")
    kwargs[key] = value


def _put_string_tuple(
    kwargs: dict[str, object],
    table: dict[str, Any],
    key: str,
) -> None:
    value = table.get(key)
    if value is None:
        return
    kwargs[key] = _string_tuple(value, key=key)


def _put_string_frozenset(
    kwargs: dict[str, object],
    table: dict[str, Any],
    key: str,
) -> None:
    value = table.get(key)
    if value is None:
        return
    kwargs[key] = frozenset(_string_tuple(value, key=key))


def _put_severity_frozenset(
    kwargs: dict[str, object],
    table: dict[str, Any],
    key: str,
) -> None:
    value = table.get(key)
    if value is None:
        return
    kwargs[key] = frozenset(_severity(value) for value in _string_tuple(value, key=key))


def _put_verification_policy(
    kwargs: dict[str, object],
    table: dict[str, Any],
) -> None:
    verification = _table(table.get("verification"))
    if not verification:
        return
    kwargs["verification_policy"] = PythonVerificationPolicy(
        profile_hints=_profile_hints(verification.get("profile_hints")),
        dependency_signals=_dependency_signals(verification.get("dependency_signals")),
        receipts=_receipts(verification.get("receipts")),
        waivers=_waivers(verification.get("waivers")),
        responsibility_task_kinds=_responsibility_task_kinds(
            verification.get("responsibility_task_kinds")
        ),
        task_contracts=_task_contracts(verification.get("task_contracts")),
        skill_bindings=_skill_bindings(verification.get("skill_bindings")),
        skill_descriptors=_skill_descriptors(verification.get("skill_descriptors")),
    )


def _profile_hints(value: object) -> tuple[PythonVerificationProfileHint, ...]:
    if not isinstance(value, list):
        return ()
    hints: list[PythonVerificationProfileHint] = []
    for item in value:
        table = _table(item)
        owner_path = table.get("owner_path")
        if not isinstance(owner_path, str):
            continue
        responsibilities = _responsibilities(table.get("responsibilities"))
        if not responsibilities:
            continue
        task_kinds = _task_kinds(table.get("task_kinds"))
        enabled = table.get("verification_tasks_enabled")
        hints.append(
            PythonVerificationProfileHint(
                owner_path=owner_path,
                responsibilities=responsibilities,
                task_kinds=task_kinds,
                verification_tasks_enabled=(
                    enabled if isinstance(enabled, bool) else True
                ),
                rationale=table.get("rationale")
                if isinstance(table.get("rationale"), str)
                else "",
                task_contracts=_task_contracts(table.get("task_contracts")),
            )
        )
    return tuple(hints)


def _dependency_signals(
    value: object,
) -> tuple[PythonVerificationDependencySignal, ...]:
    if not isinstance(value, list):
        return ()
    signals: list[PythonVerificationDependencySignal] = []
    for item in value:
        table = _table(item)
        package_name = table.get("package_name", table.get("package"))
        if not isinstance(package_name, str):
            continue
        responsibilities = _responsibilities(table.get("responsibilities"))
        if not responsibilities:
            continue
        rationale = table.get("rationale")
        signals.append(
            PythonVerificationDependencySignal(
                package_name=package_name,
                responsibilities=responsibilities,
                task_kinds=_task_kinds(table.get("task_kinds")),
                rationale=rationale if isinstance(rationale, str) else "",
            )
        )
    return tuple(signals)


def _receipts(value: object) -> tuple[PythonVerificationReceipt, ...]:
    if not isinstance(value, list):
        return ()
    receipts: list[PythonVerificationReceipt] = []
    for item in value:
        table = _table(item)
        fingerprint = table.get("task_fingerprint")
        if not isinstance(fingerprint, str):
            continue
        summary = table.get("summary")
        receipts.append(
            PythonVerificationReceipt(
                task_fingerprint=fingerprint,
                summary=summary if isinstance(summary, str) else "",
            )
        )
    return tuple(receipts)


def _waivers(value: object) -> tuple[PythonVerificationWaiver, ...]:
    if not isinstance(value, list):
        return ()
    waivers: list[PythonVerificationWaiver] = []
    for item in value:
        table = _table(item)
        fingerprint = table.get("task_fingerprint")
        rationale = table.get("rationale")
        if not isinstance(fingerprint, str) or not isinstance(rationale, str):
            continue
        waivers.append(
            PythonVerificationWaiver(
                task_fingerprint=fingerprint,
                rationale=rationale,
            )
        )
    return tuple(waivers)


def _responsibility_task_kinds(
    value: object,
) -> dict[PythonOwnerResponsibility, tuple[PythonVerificationTaskKind, ...]]:
    table = _table(value)
    result: dict[PythonOwnerResponsibility, tuple[PythonVerificationTaskKind, ...]] = {}
    for key, task_values in table.items():
        if not isinstance(key, str):
            continue
        result[_responsibility(key)] = _task_kinds(task_values)
    return result


def _task_contracts(
    value: object,
) -> dict[PythonVerificationTaskKind, PythonVerificationTaskContract]:
    table = _table(value)
    result: dict[PythonVerificationTaskKind, PythonVerificationTaskContract] = {}
    for key, contract_value in table.items():
        if not isinstance(key, str):
            continue
        contract = _task_contract(contract_value)
        if contract is None:
            continue
        result[_task_kind(key)] = contract
    return result


def _task_contract(value: object) -> PythonVerificationTaskContract | None:
    table = _table(value)
    summary = table.get("summary")
    if not isinstance(summary, str):
        return None
    phase_value = table.get("phase")
    return PythonVerificationTaskContract(
        phase=(
            _phase(phase_value)
            if isinstance(phase_value, str)
            else PythonVerificationPhase.BEFORE_RELEASE
        ),
        summary=summary,
        requirements=_requirements(table.get("requirements")),
    )


def _skill_bindings(
    value: object,
) -> dict[PythonVerificationTaskKind, PythonVerificationSkillBinding]:
    table = _table(value)
    result: dict[PythonVerificationTaskKind, PythonVerificationSkillBinding] = {}
    for key, binding_value in table.items():
        if not isinstance(key, str):
            continue
        if isinstance(binding_value, str):
            result[_task_kind(key)] = PythonVerificationSkillBinding(binding_value)
            continue
        binding_table = _table(binding_value)
        skill = binding_table.get("skill")
        if not isinstance(skill, str):
            continue
        adapter = binding_table.get("adapter")
        result[_task_kind(key)] = PythonVerificationSkillBinding(
            skill=skill,
            adapter=adapter if isinstance(adapter, str) else None,
        )
    return result


def _skill_descriptors(
    value: object,
) -> dict[str, PythonVerificationSkillDescriptor]:
    table = _table(value)
    result: dict[str, PythonVerificationSkillDescriptor] = {}
    for key, descriptor_value in table.items():
        if not isinstance(key, str):
            continue
        descriptor_table = _table(descriptor_value)
        task_kind_value = descriptor_table.get("task_kind")
        summary = descriptor_table.get("summary")
        if not isinstance(task_kind_value, str) or not isinstance(summary, str):
            continue
        adapter = descriptor_table.get("adapter")
        descriptor = PythonVerificationSkillDescriptor(
            key=key,
            task_kind=_task_kind(task_kind_value),
            summary=summary,
            adapter=adapter if isinstance(adapter, str) else None,
            requirements=_requirements(descriptor_table.get("requirements")),
        )
        result[descriptor.compact_label] = descriptor
    return result


def _requirements(value: object) -> tuple[PythonVerificationRequirement, ...]:
    if not isinstance(value, list):
        return ()
    requirements: list[PythonVerificationRequirement] = []
    for item in value:
        table = _table(item)
        label = table.get("label")
        detail = table.get("detail")
        if not isinstance(label, str) or not isinstance(detail, str):
            continue
        requirements.append(PythonVerificationRequirement(label, detail))
    return tuple(requirements)


def _responsibilities(value: object) -> tuple[PythonOwnerResponsibility, ...]:
    if value is None:
        return ()
    return tuple(
        _responsibility(item) for item in _string_tuple(value, key="responsibilities")
    )


def _task_kinds(value: object) -> tuple[PythonVerificationTaskKind, ...]:
    if value is None:
        return ()
    return tuple(_task_kind(item) for item in _string_tuple(value, key="task_kinds"))


def _responsibility(value: str) -> PythonOwnerResponsibility:
    try:
        return PythonOwnerResponsibility(value)
    except ValueError as error:
        raise ValueError(
            f"{_TOOL_TABLE_NAME}.verification has unknown responsibility: {value}"
        ) from error


def _task_kind(value: str) -> PythonVerificationTaskKind:
    try:
        return PythonVerificationTaskKind(value)
    except ValueError as error:
        raise ValueError(
            f"{_TOOL_TABLE_NAME}.verification has unknown task kind: {value}"
        ) from error


def _phase(value: str) -> PythonVerificationPhase:
    try:
        return PythonVerificationPhase(value)
    except ValueError as error:
        raise ValueError(
            f"{_TOOL_TABLE_NAME}.verification has unknown phase: {value}"
        ) from error


def _table(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _string_tuple(value: object, *, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{_TOOL_TABLE_NAME}.{key} must be a list of strings")
    values: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{_TOOL_TABLE_NAME}.{key} must be a list of strings")
        if item in seen:
            continue
        seen.add(item)
        values.append(item)
    return tuple(values)


def _severity(value: str) -> PythonDiagnosticSeverity:
    try:
        return PythonDiagnosticSeverity(value)
    except ValueError as error:
        raise ValueError(
            f"{_TOOL_TABLE_NAME}.blocking_severities has unknown severity: {value}"
        ) from error
