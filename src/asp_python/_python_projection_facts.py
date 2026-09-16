"""Primary statement projection facts for Python compact AST."""

from __future__ import annotations

import ast

from asp_python._python_expr import (
    _args,
    _aug_assign_stmt,
    _expr,
    _with_items,
)
from asp_python._python_projection_model import (
    CompactPythonProjectionNode,
    node_fact,
)


def projection_fact(
    node: ast.AST,
    *,
    owner_path: str,
    start_line: int,
    depth: int,
    parent: ast.AST | None = None,
) -> CompactPythonProjectionNode | None:
    for fact in (
        _declaration_projection_fact(node, owner_path, start_line, depth),
        _mutation_projection_fact(node, owner_path, start_line, depth, parent=parent),
        _control_flow_projection_fact(node, owner_path, start_line, depth),
        _terminal_projection_fact(node, owner_path, start_line, depth),
        _effect_projection_fact(node, owner_path, start_line, depth),
    ):
        if fact is not None:
            return fact
    return None


def _class_header(node: ast.ClassDef) -> str:
    bases = ", ".join(_expr(base) for base in node.bases)
    suffix = f"({bases})" if bases else ""
    return f"class {node.name}{suffix}:"


def _function_header(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    async_prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    returns = f" -> {_expr(node.returns)}" if node.returns is not None else ""
    return f"{async_prefix}def {node.name}({_args(node.args)}){returns}:"


def _annotation_label(node: ast.AnnAssign) -> str:
    value = f" = {_expr(node.value)}" if node.value is not None else ""
    return f"{_expr(node.target)}: {_expr(node.annotation)}{value}"


def _assign_label(node: ast.Assign) -> str:
    targets = " = ".join(_expr(target) for target in node.targets)
    return f"{targets} = {_expr(node.value)}"


def _return_label(node: ast.Return) -> str:
    return "return" if node.value is None else f"return {_expr(node.value)}"


def _raise_label(node: ast.Raise) -> str:
    return "raise" if node.exc is None else f"raise {_expr(node.exc)}"


def _declaration_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.ClassDef):
        return node_fact(
            node,
            "class",
            "declaration",
            _class_header(node),
            depth,
            owner_path,
            start_line,
        )
    if isinstance(node, ast.AsyncFunctionDef):
        return node_fact(
            node,
            "async_function",
            "declaration",
            _function_header(node),
            depth,
            owner_path,
            start_line,
            flags=("async",),
        )
    if isinstance(node, ast.FunctionDef):
        return node_fact(
            node,
            "function",
            "declaration",
            _function_header(node),
            depth,
            owner_path,
            start_line,
        )
    return None


def _mutation_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
    *,
    parent: ast.AST | None = None,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.Assign):
        return node_fact(
            node,
            "assign",
            "mutation",
            _assign_label(node),
            depth,
            owner_path,
            start_line,
            flags=("mutation",),
        )
    if isinstance(node, ast.AnnAssign):
        if isinstance(parent, ast.ClassDef):
            return node_fact(
                node,
                "field",
                "field",
                _annotation_label(node),
                depth,
                owner_path,
                start_line,
                flags=("field",),
            )
        return node_fact(
            node,
            "assign",
            "mutation",
            _annotation_label(node),
            depth,
            owner_path,
            start_line,
            flags=("mutation",),
        )
    if isinstance(node, ast.AugAssign):
        return node_fact(
            node,
            "aug_assign",
            "mutation",
            _aug_assign_stmt(node),
            depth,
            owner_path,
            start_line,
            flags=("mutation",),
        )
    return None


def _control_flow_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.If):
        return node_fact(
            node,
            "if",
            "control-flow",
            f"if {_expr(node.test)}:",
            depth,
            owner_path,
            start_line,
            flags=("branch",),
        )
    if isinstance(node, ast.For | ast.AsyncFor):
        flags = ("loop", "async") if isinstance(node, ast.AsyncFor) else ("loop",)
        async_prefix = "async " if isinstance(node, ast.AsyncFor) else ""
        return node_fact(
            node,
            "for",
            "control-flow",
            f"{async_prefix}for {_expr(node.target)} in {_expr(node.iter)}:",
            depth,
            owner_path,
            start_line,
            flags=flags,
        )
    return _compound_control_projection_fact(node, owner_path, start_line, depth)


def _compound_control_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.While):
        return node_fact(
            node,
            "while",
            "control-flow",
            f"while {_expr(node.test)}:",
            depth,
            owner_path,
            start_line,
            flags=("loop",),
        )
    if isinstance(node, ast.With | ast.AsyncWith):
        flags = ("async",) if isinstance(node, ast.AsyncWith) else ()
        async_prefix = "async " if isinstance(node, ast.AsyncWith) else ""
        return node_fact(
            node,
            "with",
            "control-flow",
            f"{async_prefix}with {_with_items(node.items)}:",
            depth,
            owner_path,
            start_line,
            flags=flags,
        )
    if isinstance(node, ast.Try):
        return node_fact(
            node, "try", "control-flow", "try:", depth, owner_path, start_line
        )
    if isinstance(node, ast.Match):
        return node_fact(
            node,
            "match",
            "control-flow",
            f"match {_expr(node.subject)}:",
            depth,
            owner_path,
            start_line,
            flags=("branch",),
        )
    if isinstance(node, ast.match_case):
        guard = f" if {_expr(node.guard)}" if node.guard is not None else ""
        return node_fact(
            node,
            "case",
            "control-flow",
            f"case {_expr(node.pattern)}{guard}:",
            depth,
            owner_path,
            start_line,
            flags=("branch",),
        )
    if isinstance(node, ast.ExceptHandler):
        label = _expr(node.type) if node.type is not None else "Exception"
        suffix = f" as {node.name}" if node.name else ""
        return node_fact(
            node,
            "except",
            "control-flow",
            f"except {label}{suffix}:",
            depth,
            owner_path,
            start_line,
            flags=("branch",),
        )
    return None


def _terminal_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.Return):
        return node_fact(
            node,
            "return",
            "terminal",
            _return_label(node),
            depth,
            owner_path,
            start_line,
            flags=_terminal_flags("return", node),
        )
    if isinstance(node, ast.Raise):
        return node_fact(
            node,
            "raise",
            "terminal",
            _raise_label(node),
            depth,
            owner_path,
            start_line,
            flags=("raise",),
        )
    return _jump_terminal_projection_fact(node, owner_path, start_line, depth)


def _jump_terminal_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.Break):
        return node_fact(
            node,
            "break",
            "terminal",
            "break",
            depth,
            owner_path,
            start_line,
            flags=("break",),
        )
    if isinstance(node, ast.Continue):
        return node_fact(
            node,
            "continue",
            "terminal",
            "continue",
            depth,
            owner_path,
            start_line,
            flags=("continue",),
        )
    return None


def _effect_projection_fact(
    node: ast.AST,
    owner_path: str,
    start_line: int,
    depth: int,
) -> CompactPythonProjectionNode | None:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        return node_fact(
            node,
            "call",
            "call",
            _expr(node.value),
            depth,
            owner_path,
            start_line,
            flags=("call",),
        )
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await):
        return node_fact(
            node,
            "await",
            "effect",
            f"await {_expr(node.value.value)}",
            depth,
            owner_path,
            start_line,
            flags=("await",),
        )
    return None


def _terminal_flags(kind: str, node: ast.AST) -> tuple[str, ...]:
    flags = [kind]
    if any(isinstance(child, ast.Await) for child in ast.walk(node)):
        flags.append("await")
    return tuple(flags)
