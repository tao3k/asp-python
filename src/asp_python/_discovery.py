"""Python project path discovery for embedded harness runs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._constants import IGNORED_DIR_NAMES, INCLUDE_HIDDEN_DIR_NAMES
from ._model import PythonProjectHarnessScope
from ._project_metadata import read_python_project_metadata

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


def discover_python_files(
    paths: Sequence[str | Path],
    *,
    ignored_dir_names: Iterable[str] | None = None,
    include_hidden_dir_names: Iterable[str] | None = None,
) -> tuple[Path, ...]:
    """Discover Python files below the provided paths."""

    ignored_names = (
        IGNORED_DIR_NAMES if ignored_dir_names is None else frozenset(ignored_dir_names)
    )
    included_hidden_names = (
        INCLUDE_HIDDEN_DIR_NAMES
        if include_hidden_dir_names is None
        else frozenset(include_hidden_dir_names)
    )
    discovered: list[Path] = []
    seen: set[Path] = set()
    for candidate in _iter_python_file_candidates(
        paths,
        ignored_dir_names=ignored_names,
        include_hidden_dir_names=included_hidden_names,
    ):
        _append_unique_path(discovered, seen, candidate)
    return tuple(sorted(discovered, key=lambda item: item.as_posix()))


def _iter_python_file_candidates(
    paths: Sequence[str | Path],
    *,
    ignored_dir_names: frozenset[str],
    include_hidden_dir_names: frozenset[str],
) -> tuple[Path, ...]:
    candidates: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if path.suffix == ".py":
                candidates.append(path)
            continue
        if path.is_dir():
            candidates.extend(
                candidate
                for candidate in path.rglob("*.py")
                if is_scannable_python_file(
                    candidate,
                    scan_root=path,
                    ignored_dir_names=ignored_dir_names,
                    include_hidden_dir_names=include_hidden_dir_names,
                )
            )
    return tuple(candidates)


def asp_python_paths(
    project_root: str | Path,
    *,
    include_tests: bool = True,
    source_dir_names: Sequence[str] = ("src",),
    test_dir_names: Sequence[str] = ("tests",),
    extra_path_names: Sequence[str] = (),
) -> tuple[Path, ...]:
    """Return project scan paths for embedded pytest harness checks."""

    return asp_python_scope(
        project_root,
        include_tests=include_tests,
        source_dir_names=source_dir_names,
        test_dir_names=test_dir_names,
        extra_path_names=extra_path_names,
    ).monitored_paths


def asp_python_scope(
    project_root: str | Path,
    *,
    include_tests: bool = True,
    source_dir_names: Sequence[str] = ("src",),
    test_dir_names: Sequence[str] = ("tests",),
    extra_path_names: Sequence[str] = (),
    ignored_dir_names: Iterable[str] | None = None,
    include_hidden_dir_names: Iterable[str] | None = None,
) -> PythonProjectHarnessScope:
    """Return the default project-wide monitoring scope."""

    root = Path(project_root)
    ignored_names = (
        IGNORED_DIR_NAMES if ignored_dir_names is None else frozenset(ignored_dir_names)
    )
    included_hidden_names = (
        INCLUDE_HIDDEN_DIR_NAMES
        if include_hidden_dir_names is None
        else frozenset(include_hidden_dir_names)
    )
    metadata = read_python_project_metadata(root)
    metadata_package_roots = () if metadata is None else metadata.package_roots
    source_paths = _source_paths(root, source_dir_names, metadata_package_roots)
    test_paths = tuple(root / name for name in test_dir_names if (root / name).exists())
    extra_paths = tuple(
        (root / name).resolve() for name in extra_path_names if (root / name).exists()
    )
    project_paths = _project_scan_paths(
        root,
        include_tests=include_tests,
        source_paths=source_paths,
        test_paths=test_paths,
        test_dir_names=test_dir_names,
        metadata_package_roots=metadata_package_roots,
        ignored_dir_names=ignored_names,
        include_hidden_dir_names=included_hidden_names,
    )
    return PythonProjectHarnessScope(
        project_root=root,
        project_metadata=metadata,
        project_paths=project_paths,
        source_paths=source_paths,
        test_paths=test_paths,
        extra_paths=extra_paths,
        include_tests=include_tests,
    )


def _project_scan_paths(
    root: Path,
    *,
    include_tests: bool,
    source_paths: tuple[Path, ...],
    test_paths: tuple[Path, ...],
    test_dir_names: Sequence[str],
    metadata_package_roots: tuple[Path, ...],
    ignored_dir_names: frozenset[str],
    include_hidden_dir_names: frozenset[str],
) -> tuple[Path, ...]:
    external_package_roots = _external_package_roots(root, metadata_package_roots)
    if metadata_package_roots:
        selected_paths = (
            (*source_paths, *test_paths)
            if include_tests
            else (*source_paths, *external_package_roots)
        )
        return _dedupe_paths(selected_paths)
    if include_tests:
        return _dedupe_paths((root, *external_package_roots))

    excluded_test_dir_names = {
        name for name in test_dir_names if (root / name).is_dir()
    }
    candidates = [
        child
        for child in sorted(root.iterdir(), key=lambda path: path.as_posix())
        if child.name not in excluded_test_dir_names
        and not _ignored_path_part(
            child.name,
            ignored_dir_names,
            include_hidden_dir_names,
        )
        and (child.suffix == ".py" or child.is_dir())
    ]
    return _dedupe_paths((*candidates, *external_package_roots))


def _source_paths(
    root: Path,
    source_dir_names: Sequence[str],
    metadata_package_roots: tuple[Path, ...],
) -> tuple[Path, ...]:
    metadata_source_paths = _metadata_source_paths(root, metadata_package_roots)
    if metadata_source_paths:
        return metadata_source_paths
    return tuple(root / name for name in source_dir_names if (root / name).exists())


def _metadata_source_paths(
    root: Path,
    package_roots: tuple[Path, ...],
) -> tuple[Path, ...]:
    return _dedupe_paths(
        _source_path_for_package_root(root, package_root)
        for package_root in package_roots
    )


def _source_path_for_package_root(root: Path, package_root: Path) -> Path:
    if package_root.name == "src":
        return package_root
    for parent in package_root.parents:
        if parent == root:
            break
        if parent.name == "src":
            return parent
    return package_root.parent


def is_scannable_python_file(
    path: Path,
    *,
    scan_root: Path,
    ignored_dir_names: frozenset[str],
    include_hidden_dir_names: frozenset[str] = INCLUDE_HIDDEN_DIR_NAMES,
) -> bool:
    """Return whether a Python file belongs to the harness-owned scan scope."""

    relative_parts = _scan_relative_parts(path, scan_root)
    return not any(
        _ignored_path_part(part, ignored_dir_names, include_hidden_dir_names)
        for part in relative_parts
    ) and not _is_test_fixture_path(relative_parts, scan_root)


def _ignored_path_part(
    part: str,
    ignored_dir_names: frozenset[str],
    include_hidden_dir_names: frozenset[str],
) -> bool:
    return part in ignored_dir_names or (
        part.startswith(".")
        and part not in {".", ".."}
        and part not in include_hidden_dir_names
    )


def _is_test_fixture_path(relative_parts: tuple[str, ...], scan_root: Path) -> bool:
    if len(relative_parts) >= 2 and relative_parts[:2] == ("tests", "fixtures"):
        return True
    return (
        scan_root.name == "tests"
        and bool(relative_parts)
        and relative_parts[0] == "fixtures"
    )


def _append_unique_path(discovered: list[Path], seen: set[Path], path: Path) -> None:
    key = path.resolve()
    if key in seen:
        return
    seen.add(key)
    discovered.append(path)


def _external_package_roots(
    root: Path,
    package_roots: tuple[Path, ...],
) -> tuple[Path, ...]:
    return tuple(
        package_root
        for package_root in package_roots
        if not _is_relative_to(package_root, root)
    )


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return tuple(deduped)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _scan_relative_parts(path: Path, scan_root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(scan_root).parts
    except ValueError:
        return path.parts
