"""Source selection helpers for Python tree-sitter query projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._tree_sitter_query_model import SyntaxQuerySelector

if TYPE_CHECKING:
    from ._model import AspPythonReport


@dataclass(frozen=True)
class SyntaxSource:
    path: Path
    source_lines: list[str]
    canonical_path: Path


@dataclass(frozen=True)
class ResolvedSelectorSource:
    path: Path
    kind: str


def resolve_selector_source(
    project_root: Path,
    selector: SyntaxQuerySelector | None,
) -> ResolvedSelectorSource | None:
    if selector is None or _selector_contains_glob(selector.path):
        return None
    candidate = Path(selector.path)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    try:
        if candidate.is_file():
            return ResolvedSelectorSource(path=candidate.resolve(), kind="file")
        if candidate.is_dir():
            return ResolvedSelectorSource(path=candidate.resolve(), kind="directory")
    except OSError:
        return None
    return None


def syntax_sources(
    report: AspPythonReport,
    resolved_selector_source: ResolvedSelectorSource | None,
) -> list[SyntaxSource]:
    if resolved_selector_source is not None:
        if resolved_selector_source.kind == "file":
            return [_source_from_path(resolved_selector_source.path)]
        if resolved_selector_source.kind == "directory":
            return [
                _source_from_path(path)
                for path in sorted(resolved_selector_source.path.rglob("*.py"))
                if path.is_file()
            ]
    return [
        SyntaxSource(
            path=Path(module.path),
            source_lines=list(module.source_lines),
            canonical_path=_canonical_path(Path(module.path)),
        )
        for module in report.modules
        if module.path is not None
    ]


def effective_selector(
    owner_path: str,
    selector: SyntaxQuerySelector | None,
    source: SyntaxSource,
    resolved_selector_source: ResolvedSelectorSource | None,
) -> SyntaxQuerySelector | None:
    if selector is None:
        return None
    if resolved_selector_source is not None and (
        (
            resolved_selector_source.kind == "file"
            and source.canonical_path == resolved_selector_source.path
        )
        or (
            resolved_selector_source.kind == "directory"
            and _path_contains(resolved_selector_source.path, source.canonical_path)
        )
    ):
        return SyntaxQuerySelector(
            path=owner_path,
            start_line=selector.start_line,
            end_line=selector.end_line,
        )
    return selector


def _source_from_path(path: Path) -> SyntaxSource:
    return SyntaxSource(
        path=path,
        source_lines=path.read_text(encoding="utf-8").splitlines(),
        canonical_path=_canonical_path(path),
    )


def _canonical_path(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _path_contains(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _selector_contains_glob(selector_path: str) -> bool:
    return any(marker in selector_path for marker in ("*", "?", "[", "]", "{", "}"))
