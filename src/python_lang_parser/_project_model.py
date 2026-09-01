"""Project metadata model parsed from Python project configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PythonProjectDependency:
    """One dependency declaration from parser-owned project metadata."""

    requirement: str
    name: str
    source: str
    group: str | None = None
    extra: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "requirement": self.requirement,
            "name": self.name,
            "source": self.source,
            "group": self.group,
            "extra": self.extra,
        }


@dataclass(frozen=True, slots=True)
class PythonProjectImportName:
    """One declared import name from Python project metadata."""

    name: str
    namespace: tuple[str, ...]
    is_private: bool = False
    source_value: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "name": self.name,
            "namespace": list(self.namespace),
            "is_private": self.is_private,
            "source_value": self.source_value,
        }


@dataclass(frozen=True, slots=True)
class PythonProjectScript:
    """One console or GUI script declared by a Python project."""

    name: str
    target: str
    kind: str
    target_module: str = ""
    target_namespace: tuple[str, ...] = ()
    target_object: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "name": self.name,
            "target": self.target,
            "kind": self.kind,
            "target_module": self.target_module,
            "target_namespace": list(self.target_namespace),
            "target_object": list(self.target_object),
        }


@dataclass(frozen=True, slots=True)
class PythonProjectEntryPoint:
    """One arbitrary entry point declared by a Python project."""

    group: str
    name: str
    target: str
    target_module: str = ""
    target_namespace: tuple[str, ...] = ()
    target_object: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "group": self.group,
            "name": self.name,
            "target": self.target,
            "target_module": self.target_module,
            "target_namespace": list(self.target_namespace),
            "target_object": list(self.target_object),
        }


@dataclass(frozen=True, slots=True)
class PythonPytestOptions:
    """Parser-owned pytest options from `pyproject.toml`."""

    addopts: tuple[str, ...] = ()

    @property
    def enables_asp_python(self) -> bool:
        """Return whether pytest addopts mounts the project harness plugin."""

        return "--python-project-harness" in self.addopts

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "addopts": list(self.addopts),
            "enables_asp_python": self.enables_asp_python,
        }


@dataclass(frozen=True, slots=True)
class PythonProjectMetadata:
    """Compact `pyproject.toml` metadata needed by parser consumers."""

    project_root: Path
    pyproject_path: Path
    has_project_table: bool
    has_build_system_table: bool
    project_name: str | None
    requires_python: str | None
    build_backend: str | None
    build_requires: tuple[str, ...]
    wheel_packages: tuple[str, ...]
    package_roots: tuple[Path, ...]
    dependencies: tuple[PythonProjectDependency, ...] = ()
    import_names: tuple[PythonProjectImportName, ...] = ()
    import_namespaces: tuple[PythonProjectImportName, ...] = ()
    scripts: tuple[PythonProjectScript, ...] = ()
    gui_scripts: tuple[PythonProjectScript, ...] = ()
    entry_points: tuple[PythonProjectEntryPoint, ...] = ()
    pytest_options: PythonPytestOptions = PythonPytestOptions()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""

        return {
            "project_root": str(self.project_root),
            "pyproject_path": str(self.pyproject_path),
            "has_project_table": self.has_project_table,
            "has_build_system_table": self.has_build_system_table,
            "project_name": self.project_name,
            "requires_python": self.requires_python,
            "build_backend": self.build_backend,
            "build_requires": list(self.build_requires),
            "dependencies": [item.to_dict() for item in self.dependencies],
            "wheel_packages": list(self.wheel_packages),
            "package_roots": [str(path) for path in self.package_roots],
            "import_names": [item.to_dict() for item in self.import_names],
            "import_namespaces": [item.to_dict() for item in self.import_namespaces],
            "scripts": [item.to_dict() for item in self.scripts],
            "gui_scripts": [item.to_dict() for item in self.gui_scripts],
            "entry_points": [item.to_dict() for item in self.entry_points],
            "pytest_options": self.pytest_options.to_dict(),
        }
