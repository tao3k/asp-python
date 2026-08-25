"""Search runtime helpers for the Python harness CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._cli_args import ProtocolArgs

_KNOWLEDGE_VIEWS = frozenset(
    {
        "env",
        "runtime-source",
        "lang",
        "std",
        "capability",
        "extension",
        "pattern",
        "compare",
    }
)
_QUERY_PREFILTER_VIEWS = frozenset(
    {
        "api",
        "callsite",
        "import",
        "public-external-types",
        "policy",
        "symbol",
        "tests",
    }
)


def _run_search_harness(
    project_root: Path,
    args: ProtocolArgs,
) -> tuple[object, dict[str, object] | None]:
    owner_items_report = _run_exact_owner_items_search(project_root, args)
    if owner_items_report is not None:
        return owner_items_report, {
            "reason": "owner-items-exact-owner-prefilter",
            "fields": {
                "paths": 1,
                "ownerPath": _owner_items_query_path(args) or "",
            },
        }
    owner_report = _run_exact_owner_search(project_root, args)
    if owner_report is not None:
        return owner_report, {
            "reason": "owner-exact-path-prefilter",
            "fields": {
                "paths": 1,
                "ownerPath": _owner_query_path(args) or "",
            },
        }
    dependency_report = _run_metadata_dependency_search(project_root, args)
    if dependency_report is not None:
        return dependency_report, {
            "reason": "dependency-metadata-prefilter",
            "fields": {
                "paths": 0,
                "dependency": args.query or "",
            },
        }
    workspace_seed_report = _run_workspace_seed_metadata_search(project_root, args)
    if workspace_seed_report is not None:
        return workspace_seed_report, {
            "reason": "workspace-seed-metadata-route",
            "fields": {"paths": 0, "view": args.view or ""},
        }
    metadata_report = _run_metadata_only_search(project_root, args)
    if metadata_report is not None:
        return metadata_report, {
            "reason": "knowledge-metadata-route",
            "fields": {"paths": 0, "view": args.view or ""},
        }
    from ._rule_packs import resolve_project_harness_config

    config = resolve_project_harness_config(
        project_root,
        None,
        rule_packs=None,
    )
    if args.command != "search":
        from ._runner import run_python_project_harness

        return run_python_project_harness(project_root, config=config), None
    if config.include_hidden_dir_names:
        from ._runner import run_python_project_harness

        return run_python_project_harness(project_root, config=config), None
    query_terms = _prefilter_query_terms(args)
    if query_terms is None:
        from ._runner import run_python_project_harness

        return run_python_project_harness(project_root, config=config), None
    from ._semantic_search_prefilter import prefilter_python_text_search_paths

    prefilter = prefilter_python_text_search_paths(
        project_root,
        query_terms,
        owner_path=args.owner_path,
    )
    if prefilter is None:
        from ._runner import run_python_project_harness

        return run_python_project_harness(project_root, config=config), None
    return _run_prefiltered_text_search(project_root, prefilter.paths), (
        prefilter.runtime_cost()
    )


def _prefilter_query_terms(args: ProtocolArgs) -> tuple[str, ...] | None:
    if args.view == "lexical":
        return args.query_set or (
            () if args.query is None else tuple(args.query.split())
        )
    if (
        args.view == "reasoning"
        and args.query == "query-deps"
        and args.item_query is not None
        and args.dependency is not None
    ):
        return (args.item_query, args.dependency)
    if args.view in _QUERY_PREFILTER_VIEWS and args.query is not None:
        return (args.query,)
    return None


def _run_exact_owner_items_search(
    project_root: Path,
    args: ProtocolArgs,
) -> _TextSearchReport | None:
    owner_path = _exact_owner_items_path(project_root, args)
    if owner_path is None:
        return None
    from python_lang_parser.parser import parse_python_file

    return _TextSearchReport(
        modules=(parse_python_file(owner_path),),
        project_resolution=_fast_owner_items_scope(project_root, owner_path),
        root_paths=(str(owner_path),),
    )


def _run_exact_owner_search(
    project_root: Path,
    args: ProtocolArgs,
) -> _TextSearchReport | None:
    owner_path = _exact_owner_path(project_root, args)
    if owner_path is None:
        return None
    from python_lang_parser.parser import parse_python_file

    paths = _exact_owner_related_paths(project_root, owner_path)
    return _TextSearchReport(
        modules=tuple(parse_python_file(path) for path in paths),
        project_resolution=_fast_text_search_scope(project_root),
        root_paths=tuple(str(path) for path in paths),
    )


def _run_metadata_dependency_search(
    project_root: Path,
    args: ProtocolArgs,
) -> _TextSearchReport | None:
    if (
        args.command != "search"
        or args.view not in {"dependency", "deps"}
        or args.query is None
        or "::" in args.query
    ):
        return None
    from ._project_metadata import read_python_project_metadata

    return _TextSearchReport(
        modules=(),
        project_resolution=_TextSearchScope(
            project_root=project_root,
            project_metadata=read_python_project_metadata(project_root),
            fallback_paths=(project_root,),
        ),
        root_paths=(str(project_root),),
    )


def _run_metadata_only_search(
    project_root: Path, args: ProtocolArgs
) -> _TextSearchReport | None:
    if args.command != "search" or args.view not in _KNOWLEDGE_VIEWS:
        return None
    from ._project_metadata import read_python_project_metadata

    return _TextSearchReport(
        modules=(),
        project_resolution=_TextSearchScope(
            project_root=project_root,
            project_metadata=read_python_project_metadata(project_root),
            fallback_paths=(project_root,),
        ),
        root_paths=(str(project_root),),
    )


def _run_workspace_seed_metadata_search(
    project_root: Path, args: ProtocolArgs
) -> _TextSearchReport | None:
    if (
        args.command != "search"
        or args.view != "workspace"
        or args.render_mode != "seeds"
    ):
        return None
    from ._project_metadata import read_python_project_metadata

    return _TextSearchReport(
        modules=(),
        project_resolution=_TextSearchScope(
            project_root=project_root,
            project_metadata=read_python_project_metadata(project_root),
            fallback_paths=(project_root,),
        ),
        root_paths=(str(project_root),),
    )


def _exact_owner_items_path(project_root: Path, args: ProtocolArgs) -> Path | None:
    if (
        args.command != "search"
        or args.view != "owner"
        or "items" not in args.pipes
        or _owner_items_query_path(args) is None
    ):
        return None
    raw_path = Path(_owner_items_query_path(args) or "")
    owner_path = raw_path if raw_path.is_absolute() else project_root / raw_path
    try:
        resolved_root = project_root.resolve()
        resolved_owner = owner_path.resolve()
        resolved_owner.relative_to(resolved_root)
    except ValueError:
        return None
    if not resolved_owner.is_file() or resolved_owner.suffix != ".py":
        return None
    return resolved_owner


def _exact_owner_path(project_root: Path, args: ProtocolArgs) -> Path | None:
    if (
        args.command != "search"
        or args.view != "owner"
        or args.pipes
        or _owner_query_path(args) is None
    ):
        return None
    return _resolve_project_python_file(
        project_root, Path(_owner_query_path(args) or "")
    )


def _owner_items_query_path(args: ProtocolArgs) -> str | None:
    return args.owner_path or args.query


def _owner_query_path(args: ProtocolArgs) -> str | None:
    return args.query


def _resolve_project_python_file(project_root: Path, raw_path: Path) -> Path | None:
    owner_path = raw_path if raw_path.is_absolute() else project_root / raw_path
    try:
        resolved_root = project_root.resolve()
        resolved_owner = owner_path.resolve()
        resolved_owner.relative_to(resolved_root)
    except ValueError:
        return None
    if not resolved_owner.is_file() or resolved_owner.suffix != ".py":
        return None
    return resolved_owner


def _exact_owner_related_paths(
    project_root: Path, owner_path: Path
) -> tuple[Path, ...]:
    project_root = project_root.resolve()
    owner_path = owner_path.resolve()
    paths = [owner_path]
    try:
        owner_module = owner_path.relative_to(project_root).with_suffix("")
    except ValueError:
        return tuple(paths)
    owner_parts = tuple(part for part in owner_module.parts if part != "__init__")
    if owner_parts[:1] == ("src",):
        owner_parts = owner_parts[1:]
    module_tail = ".".join(owner_parts)
    if not module_tail:
        return tuple(paths)
    import_markers = (
        f"import {module_tail}",
        f"from {module_tail} import",
        f"from .{owner_path.stem} import",
    )
    for path in sorted(project_root.rglob("*.py")):
        if path == owner_path or any(part.startswith(".") for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(marker in text for marker in import_markers):
            paths.append(path)
    return tuple(dict.fromkeys(paths))


@dataclass(frozen=True, slots=True)
class _TextSearchReport:
    modules: tuple[object, ...]
    project_resolution: _TextSearchScope
    findings: tuple[object, ...] = ()
    root_paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _TextSearchScope:
    project_root: Path
    source_paths: tuple[Path, ...] = ()
    test_paths: tuple[Path, ...] = ()
    project_metadata: object | None = None
    project_paths: tuple[Path, ...] = ()
    extra_paths: tuple[Path, ...] = ()
    include_tests: bool = True
    fallback_paths: tuple[Path, ...] = ()

    @property
    def monitored_paths(self) -> tuple[Path, ...]:
        selected = (
            (*self.source_paths, *self.test_paths, *self.extra_paths)
            if self.include_tests
            else (*self.source_paths, *self.extra_paths)
        )
        return selected or self.fallback_paths


def _run_prefiltered_text_search(
    project_root: Path,
    paths: tuple[Path, ...],
) -> _TextSearchReport:
    from python_lang_parser.parser import parse_python_file

    return _TextSearchReport(
        modules=tuple(parse_python_file(path) for path in paths),
        project_resolution=_fast_text_search_scope(project_root),
        root_paths=tuple(str(path) for path in paths),
    )


def _fast_text_search_scope(project_root: Path) -> _TextSearchScope:
    source_paths = tuple(
        path for name in ("src",) for path in (project_root / name,) if path.exists()
    )
    test_paths = tuple(
        path for name in ("tests",) for path in (project_root / name,) if path.exists()
    )
    return _TextSearchScope(
        project_root=project_root,
        source_paths=source_paths,
        test_paths=test_paths,
        fallback_paths=(project_root,),
    )


def _fast_owner_items_scope(project_root: Path, owner_path: Path) -> _TextSearchScope:
    return _TextSearchScope(
        project_root=project_root,
        fallback_paths=(owner_path,),
    )
