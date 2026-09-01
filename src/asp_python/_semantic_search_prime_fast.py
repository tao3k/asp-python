"""Fast compact frontiers for Python search prime seed view."""

from __future__ import annotations

import os
from collections import deque
from pathlib import Path

from ._cli_args import ProtocolArgs

_MAX_FAST_PRIME_OWNERS = 12
_MAX_FAST_PRIME_DIRS = 128
_MAX_FAST_PRIME_FILES = 512
_SKIPPED_DIR_NAMES = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "target",
        "venv",
    }
)
_PREFERRED_DIRS = (
    "src",
    "tests",
    "test",
    "scripts",
    "tools",
)


def render_fast_prime_search(args: ProtocolArgs, project_root: Path) -> str | None:
    """Render prime seeds without running the full project harness."""

    if not _supports_fast_prime_search(args):
        return None
    owners = _discover_python_owner_paths(project_root)
    return _render_fast_prime_seed_text(project_root, owners)


def _supports_fast_prime_search(args: ProtocolArgs) -> bool:
    return (
        args.command == "search"
        and args.view == "prime"
        and args.render_mode == "seeds"
        and not args.json
        and args.query is None
        and args.item_query is None
        and args.owner_path is None
        and not args.query_set
        and not args.pipes
    )


def _discover_python_owner_paths(project_root: Path) -> tuple[str, ...]:
    root = project_root.resolve()
    owners: list[str] = []
    seen: set[Path] = set()
    for start in _candidate_roots(root):
        _scan_python_files(start, root=root, owners=owners, seen=seen)
        if len(owners) >= _MAX_FAST_PRIME_OWNERS:
            break
    return tuple(owners[:_MAX_FAST_PRIME_OWNERS])


def _candidate_roots(root: Path) -> tuple[Path, ...]:
    selected: list[Path] = []
    for name in _PREFERRED_DIRS:
        candidate = root / name
        if candidate.exists():
            selected.append(candidate)
    if root not in selected:
        selected.append(root)
    return tuple(selected)


def _scan_python_files(
    start: Path,
    *,
    root: Path,
    owners: list[str],
    seen: set[Path],
) -> None:
    if len(owners) >= _MAX_FAST_PRIME_OWNERS:
        return
    queue: deque[Path] = deque((start,))
    visited_dirs = 0
    visited_files = 0
    while queue and len(owners) < _MAX_FAST_PRIME_OWNERS:
        directory = queue.popleft()
        try:
            resolved_dir = directory.resolve()
        except OSError:
            continue
        if resolved_dir in seen:
            continue
        seen.add(resolved_dir)
        if directory.name in _SKIPPED_DIR_NAMES:
            continue
        visited_dirs += 1
        if visited_dirs > _MAX_FAST_PRIME_DIRS:
            return
        try:
            entries = list(os.scandir(directory))
        except OSError:
            continue
        dirs: list[Path] = []
        files: list[str] = []
        for entry in entries:
            name = entry.name
            if name.startswith(".") and name not in {"."}:
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    if name not in _SKIPPED_DIR_NAMES:
                        dirs.append(Path(entry.path))
                    continue
                if entry.is_file(follow_symlinks=False) and name.endswith(".py"):
                    files.append(entry.path)
            except OSError:
                continue
        for file_path in sorted(files):
            visited_files += 1
            if visited_files > _MAX_FAST_PRIME_FILES:
                return
            owners.append(_relative_owner_path(Path(file_path), root))
            if len(owners) >= _MAX_FAST_PRIME_OWNERS:
                return
        queue.extend(sorted(dirs, key=lambda path: path.as_posix()))


def _relative_owner_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _render_fast_prime_seed_text(project_root: Path, owners: tuple[str, ...]) -> str:
    root_label = project_root.name or "."
    lines = [
        (
            f"[search-prime] root={root_label} alg=fast-prime-frontier-v1 "
            f"budget=owners:{_MAX_FAST_PRIME_OWNERS} mode=seeds"
        ),
        (
            "|decision purpose=decision-primer answer=false code=false "
            "capabilities=pipe,lexical,fd-query,rg-query,owner-items,selector-code,treesitter-query "
            "ladder=pipe>lexical>fd-query|rg-query>owner-items>selector-code "
            "history=asp-artifacts:directReadRisk,repeatedPrime,repeatedPipe,bestPath "
            "risk=broad-direct-read,manual-window-scan,repeat-prime "
            "next=\"asp python search pipe '<question-or-feature-term>' --workspace . --view seeds\""
        ).replace(
            "--workspace . --view seeds", "--workspace <workspace-root> --view seeds"
        ),
        "legend: ID=kind:role(value)!next; entries profile(selectors=>returns); frontier ID.next",
        "aliases: graph:{G=search,O=owner}",
    ]
    owner_ids = [f"O{index}" for index, _ in enumerate(owners, start=1)]
    if owners:
        lines.append(
            ";".join(
                f"{owner_id}=owner:path({owner})!owner"
                for owner_id, owner in zip(owner_ids, owners, strict=True)
            )
        )
        lines.append(
            "G>{" + ",".join(f"{owner_id}:selects" for owner_id in owner_ids) + "}"
        )
    else:
        lines.append("G>{}")
    rank = ",".join(owner_ids)
    frontier = ",".join(f"{owner_id}.owner" for owner_id in owner_ids)
    lines.extend(
        [
            f"rank={rank} frontier={frontier}",
            "entries=owner-tests(O=>covering-tests+test-entrypoints+fixtures)",
            "omit=items,blocks,code,full-json reason=fast-seeds-frontier",
        ]
    )
    return "\n".join(lines) + "\n"
