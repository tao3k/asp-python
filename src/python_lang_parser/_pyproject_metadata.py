"""Parser-owned reader for standard Python project metadata."""

from __future__ import annotations

import shlex
import tomllib
from pathlib import Path
from typing import Any

from ._project_model import (
    PythonProjectDependency,
    PythonProjectEntryPoint,
    PythonProjectImportName,
    PythonProjectMetadata,
    PythonProjectScript,
    PythonPytestOptions,
)


def parse_python_project_metadata(
    project_root: str | Path,
) -> PythonProjectMetadata | None:
    """Parse project-level metadata from `pyproject.toml` when present."""

    root = Path(project_root)
    pyproject_path = root / "pyproject.toml"
    try:
        payload = parse_python_pyproject_document(pyproject_path)
    except PythonPyprojectParseError:
        return None
    return _metadata_from_payload(root, pyproject_path, payload)


class PythonPyprojectParseError(ValueError):
    """Raised when a pyproject document cannot be parsed by the Python parser."""


def parse_python_pyproject_document(path: str | Path) -> dict[str, Any]:
    """Return the complete pyproject document or raise a parser-owned error."""
    pyproject_path = Path(path)
    if not pyproject_path.is_file():
        raise PythonPyprojectParseError(
            f"Python pyproject document is missing: {pyproject_path}"
        )
    try:
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise PythonPyprojectParseError(
            f"failed to parse Python pyproject document `{pyproject_path}`: {error}"
        ) from error


def _metadata_from_payload(
    root: Path,
    pyproject_path: Path,
    payload: dict[str, Any],
) -> PythonProjectMetadata:
    has_project_table = isinstance(payload.get("project"), dict)
    has_build_system_table = isinstance(payload.get("build-system"), dict)
    project = _table(payload.get("project"))
    build_system = _table(payload.get("build-system"))
    dependency_groups = _table(payload.get("dependency-groups"))
    tool = _table(payload.get("tool"))
    wheel_packages = _hatch_wheel_packages(payload)
    import_names = _project_import_names(project.get("import-names"))
    import_namespaces = _project_import_names(project.get("import-namespaces"))

    return PythonProjectMetadata(
        project_root=root,
        pyproject_path=pyproject_path,
        has_project_table=has_project_table,
        has_build_system_table=has_build_system_table,
        project_name=_string_or_none(project.get("name")),
        requires_python=_string_or_none(project.get("requires-python")),
        build_backend=_string_or_none(build_system.get("build-backend")),
        build_requires=_string_tuple(build_system.get("requires")),
        wheel_packages=wheel_packages,
        package_roots=_package_roots(
            root,
            wheel_packages=wheel_packages,
            import_names=import_names,
        ),
        import_names=import_names,
        import_namespaces=import_namespaces,
        scripts=_project_scripts(project.get("scripts"), kind="console"),
        gui_scripts=_project_scripts(project.get("gui-scripts"), kind="gui"),
        entry_points=_project_entry_points(project.get("entry-points")),
        dependencies=_project_dependencies(project, dependency_groups),
        pytest_options=_pytest_options(tool),
    )


def _hatch_wheel_packages(payload: dict[str, Any]) -> tuple[str, ...]:
    tool = _table(payload.get("tool"))
    hatch = _table(tool.get("hatch"))
    hatch_build = _table(hatch.get("build"))
    hatch_targets = _table(hatch_build.get("targets"))
    wheel = _table(hatch_targets.get("wheel"))
    return _string_tuple(wheel.get("packages"))


def _package_roots(
    project_root: Path,
    *,
    wheel_packages: tuple[str, ...],
    import_names: tuple[PythonProjectImportName, ...],
) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for package_path in wheel_packages:
        _append_path(roots, seen, _resolve_package_path(project_root, package_path))
    for import_name in import_names:
        if import_name.name == "":
            continue
        for package_path in _package_paths_for_import_name(project_root, import_name):
            _append_path(roots, seen, package_path)
    return tuple(roots)


def _package_paths_for_import_name(
    project_root: Path,
    import_name: PythonProjectImportName,
) -> tuple[Path, ...]:
    relative = Path(*import_name.namespace)
    candidates = (
        project_root / "src" / relative,
        project_root / relative,
    )
    return tuple(
        candidate
        for candidate in candidates
        if candidate.is_dir() and (candidate / "__init__.py").is_file()
    )


def _project_import_names(value: object) -> tuple[PythonProjectImportName, ...]:
    if not isinstance(value, list):
        return ()
    names: list[PythonProjectImportName] = []
    seen: set[tuple[str, bool]] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        parsed = _project_import_name(item)
        key = (parsed.name, parsed.is_private)
        if key in seen:
            continue
        seen.add(key)
        names.append(parsed)
    return tuple(names)


def _project_import_name(value: str) -> PythonProjectImportName:
    name_part, _, modifier_part = value.partition(";")
    name = name_part.strip()
    modifier = modifier_part.strip().lower()
    return PythonProjectImportName(
        name=name,
        namespace=tuple(part for part in name.split(".") if part),
        is_private=modifier == "private",
        source_value=value,
    )


def _project_scripts(value: object, *, kind: str) -> tuple[PythonProjectScript, ...]:
    table = _table(value)
    scripts: list[PythonProjectScript] = []
    for name, target in sorted(table.items()):
        if not isinstance(name, str) or not isinstance(target, str):
            continue
        target_facts = _target_facts(target)
        scripts.append(
            PythonProjectScript(
                name=name,
                target=target,
                kind=kind,
                target_module=target_facts[0],
                target_namespace=target_facts[1],
                target_object=target_facts[2],
            )
        )
    return tuple(scripts)


def _project_entry_points(value: object) -> tuple[PythonProjectEntryPoint, ...]:
    table = _table(value)
    entry_points: list[PythonProjectEntryPoint] = []
    for group, entries_value in sorted(table.items()):
        entries = _table(entries_value)
        for name, target in sorted(entries.items()):
            if not isinstance(group, str) or not isinstance(name, str):
                continue
            if not isinstance(target, str):
                continue
            target_facts = _target_facts(target)
            entry_points.append(
                PythonProjectEntryPoint(
                    group=group,
                    name=name,
                    target=target,
                    target_module=target_facts[0],
                    target_namespace=target_facts[1],
                    target_object=target_facts[2],
                )
            )
    return tuple(entry_points)


def _project_dependencies(
    project: dict[str, Any],
    dependency_groups: dict[str, Any],
) -> tuple[PythonProjectDependency, ...]:
    dependencies: list[PythonProjectDependency] = []
    seen: set[tuple[str, str, str | None, str | None]] = set()
    _extend_dependencies(
        dependencies,
        seen,
        project.get("dependencies"),
        source="project.dependencies",
    )
    optional_dependencies = _table(project.get("optional-dependencies"))
    for extra, value in sorted(optional_dependencies.items()):
        if not isinstance(extra, str):
            continue
        _extend_dependencies(
            dependencies,
            seen,
            value,
            source="project.optional-dependencies",
            extra=extra,
        )
    for group, value in sorted(dependency_groups.items()):
        if not isinstance(group, str):
            continue
        _extend_dependencies(
            dependencies,
            seen,
            value,
            source="dependency-groups",
            group=group,
        )
    return tuple(dependencies)


def _extend_dependencies(
    dependencies: list[PythonProjectDependency],
    seen: set[tuple[str, str, str | None, str | None]],
    value: object,
    *,
    source: str,
    group: str | None = None,
    extra: str | None = None,
) -> None:
    if not isinstance(value, list):
        return
    for item in value:
        if isinstance(item, str):
            requirement = item.strip()
        elif isinstance(item, dict):
            requirement = _dependency_object_requirement(item)
        else:
            continue
        if not requirement:
            continue
        dependency = PythonProjectDependency(
            requirement=requirement,
            name=_dependency_name(requirement),
            source=source,
            group=group,
            extra=extra,
        )
        key = (
            dependency.requirement,
            dependency.source,
            dependency.group,
            dependency.extra,
        )
        if key in seen:
            continue
        seen.add(key)
        dependencies.append(dependency)


def _dependency_object_requirement(value: dict[str, Any]) -> str:
    dependency = value.get("dependency")
    if isinstance(dependency, str):
        return dependency.strip()
    package = value.get("package")
    if isinstance(package, str):
        return package.strip()
    return ""


def _dependency_name(requirement: str) -> str:
    name = requirement.split(";", 1)[0].split("[", 1)[0].strip()
    for marker in ("<", ">", "=", "!", "~", " "):
        name = name.split(marker, 1)[0].strip()
    return name


def _pytest_options(tool: dict[str, Any]) -> PythonPytestOptions:
    pytest_table = _table(tool.get("pytest"))
    ini_options = _table(pytest_table.get("ini_options"))
    return PythonPytestOptions(addopts=_pytest_addopts(ini_options.get("addopts")))


def _pytest_addopts(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        try:
            return tuple(shlex.split(value))
        except ValueError:
            return tuple(part for part in value.split() if part)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str))
    return ()


def _target_facts(target: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    target_without_extras = target.split("[", 1)[0].strip()
    module_part, _, object_part = target_without_extras.partition(":")
    module = module_part.strip()
    return (
        module,
        tuple(part for part in module.split(".") if part),
        tuple(part for part in object_part.strip().split(".") if part),
    )


def _table(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    seen: set[str] = set()
    values: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        package_path = Path(item).as_posix()
        if package_path in seen:
            continue
        seen.add(package_path)
        values.append(package_path)
    return tuple(values)


def _resolve_package_path(project_root: Path, package_path: str) -> Path:
    path = Path(package_path)
    if path.is_absolute():
        return path
    return project_root / path


def _append_path(paths: list[Path], seen: set[Path], path: Path) -> None:
    key = path.resolve()
    if key in seen:
        return
    seen.add(key)
    paths.append(path)
