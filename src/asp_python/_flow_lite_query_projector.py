"""Python AST source/sink projection for flow-lite queries."""

from __future__ import annotations

import ast
from pathlib import Path

from ._flow_lite_query_model import _FlowLiteOccurrence, _FlowLiteResult

_PYTHON_SUFFIX = ".py"
_IGNORED_DIR_NAMES = frozenset(
    {
        ".cache",
        ".devenv",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)


def _evaluate_flow_lite_query(
    project_root: Path, where: dict[str, str]
) -> _FlowLiteResult:
    files = _python_source_files(project_root)
    for path in files:
        result = _flow_lite_result_for_file(path, project_root, where)
        if result is not None:
            result["scanned_files"] = len(files)
            return result
    return {
        "owner_path": ".",
        "function_start": 1,
        "function_end": 1,
        "source": None,
        "sink": None,
        "scanned_files": len(files),
    }


def _flow_lite_result_for_file(
    path: Path,
    project_root: Path,
    where: dict[str, str],
) -> _FlowLiteResult | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    owner_path = _project_path(path, project_root)
    return _find_flow_lite_function(tree, owner_path, where)


def _find_flow_lite_function(
    tree: ast.Module,
    owner_path: str,
    where: dict[str, str],
) -> _FlowLiteResult | None:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == where["scope.fn"]
        ):
            return _flow_lite_result_for_function(node, owner_path, where)
    return None


def _flow_lite_result_for_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    owner_path: str,
    where: dict[str, str],
) -> _FlowLiteResult:
    calls = [child for child in ast.walk(node) if isinstance(child, ast.Call)]
    return {
        "owner_path": owner_path,
        "function_start": node.lineno,
        "function_end": getattr(node, "end_lineno", node.lineno),
        "source": _first_call_occurrence(
            calls, "call", where["source.call"], owner_path
        ),
        "sink": _first_call_occurrence(
            calls, "constructs", where["sink.constructs"], owner_path
        ),
        "scanned_files": 0,
    }


def _first_call_occurrence(
    calls: list[ast.Call],
    kind: str,
    target: str,
    owner_path: str,
) -> _FlowLiteOccurrence | None:
    for call in calls:
        if _call_target_name(call.func) == target:
            return _flow_lite_occurrence(kind, target, owner_path, call.lineno)
    return None


def _python_source_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    pending = [project_root]
    while pending:
        current = pending.pop()
        if _ignored_path(current):
            continue
        if current.is_dir():
            pending.extend(sorted(current.iterdir(), reverse=True))
            continue
        if current.is_file() and current.suffix == _PYTHON_SUFFIX:
            files.append(current)
    return sorted(files)


def _ignored_path(path: Path) -> bool:
    return any(
        part in _IGNORED_DIR_NAMES or part.startswith(".") for part in path.parts
    )


def _project_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return "external/" + path.name


def _call_target_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ast.unparse(node)


def _flow_lite_occurrence(
    kind: str,
    value: str,
    owner_path: str,
    line: int,
) -> _FlowLiteOccurrence:
    return {
        "handle": f"{kind}:{value}@{owner_path}:{line}",
        "kind": kind,
        "value": value,
        "path": owner_path,
        "line": line,
    }
