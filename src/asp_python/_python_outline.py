"""Render compact Python outline code from native AST statements."""

from __future__ import annotations

import ast

from asp_python._python_expr import (
    _args,
    _aug_assign_stmt,
    _expr,
    _import_stmt,
    _targets,
    _with_items,
)


def render_python_outline(tree: ast.Module) -> str:
    """Render parser-owned compact outline code for a parsed Python module."""

    renderer = _PythonOutlineRenderer()
    return renderer.render(tree)


def fallback_python_compact(raw_lines: list[str]) -> str:
    """Return indentation-trimmed source when native parsing cannot proceed."""

    selected = [line.rstrip() for line in raw_lines if line.strip()]
    if not selected:
        return ""
    base_indent = min(_leading_spaces(line) for line in selected)
    return "\n".join(_trim_python_line(line, base_indent) for line in selected)


class _PythonOutlineRenderer:
    def __init__(self) -> None:
        self._lines: list[str] = []

    def render(self, tree: ast.Module) -> str:
        for node in tree.body:
            self._append_node(node, depth=0)
        return "\n".join(line.rstrip() for line in self._lines if line.strip())

    def _append_node(self, node: ast.AST, *, depth: int) -> None:
        if _is_docstring_expr(node):
            return
        prefix = "  " * depth
        for append in (
            self._append_declaration,
            self._append_assignment,
            self._append_control_flow,
            self._append_terminal,
        ):
            if append(node, prefix=prefix, depth=depth):
                return
        self._lines.append(f"{prefix}{node.__class__.__name__}")

    def _append_declaration(
        self,
        node: ast.AST,
        *,
        prefix: str,
        depth: int,
    ) -> bool:
        if isinstance(node, ast.ClassDef):
            self._append_decorators(node.decorator_list, prefix)
            bases = ", ".join(_expr(base) for base in node.bases)
            suffix = f"({bases})" if bases else ""
            self._lines.append(f"{prefix}class {node.name}{suffix}:")
            self._append_block(node.body, depth=depth + 1)
            return True
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            self._append_decorators(node.decorator_list, prefix)
            async_prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            returns = f" -> {_expr(node.returns)}" if node.returns is not None else ""
            self._lines.append(
                f"{prefix}{async_prefix}def {node.name}({_args(node.args)}){returns}:"
            )
            self._append_block(node.body, depth=depth + 1)
            return True
        return False

    def _append_decorators(self, decorators: list[ast.expr], prefix: str) -> None:
        for decorator in decorators:
            self._lines.append(f"{prefix}@{_expr(decorator)}")

    def _append_assignment(
        self,
        node: ast.AST,
        *,
        prefix: str,
        depth: int,
    ) -> bool:
        del depth
        if isinstance(node, ast.Assign):
            self._lines.append(
                f"{prefix}{_targets(node.targets)} = {_expr(node.value)}"
            )
            return True
        if isinstance(node, ast.AnnAssign):
            target = _expr(node.target)
            annotation = _expr(node.annotation)
            value = f" = {_expr(node.value)}" if node.value is not None else ""
            self._lines.append(f"{prefix}{target}: {annotation}{value}")
            return True
        if isinstance(node, ast.AugAssign):
            self._lines.append(f"{prefix}{_aug_assign_stmt(node)}")
            return True
        if isinstance(node, ast.Import | ast.ImportFrom):
            self._lines.append(f"{prefix}{_import_stmt(node)}")
            return True
        return False

    def _append_control_flow(
        self,
        node: ast.AST,
        *,
        prefix: str,
        depth: int,
    ) -> bool:
        if isinstance(node, ast.If):
            self._append_if(node, prefix=prefix, depth=depth)
            return True
        if isinstance(node, ast.For | ast.AsyncFor):
            async_prefix = "async " if isinstance(node, ast.AsyncFor) else ""
            self._lines.append(
                f"{prefix}{async_prefix}for {_expr(node.target)} in {_expr(node.iter)}:"
            )
            self._append_block(node.body, depth=depth + 1)
            return True
        if isinstance(node, ast.While):
            self._lines.append(f"{prefix}while {_expr(node.test)}:")
            self._append_block(node.body, depth=depth + 1)
            return True
        if isinstance(node, ast.With | ast.AsyncWith):
            async_prefix = "async " if isinstance(node, ast.AsyncWith) else ""
            self._lines.append(f"{prefix}{async_prefix}with {_with_items(node.items)}:")
            self._append_block(node.body, depth=depth + 1)
            return True
        return self._append_exception_or_match(node, prefix=prefix, depth=depth)

    def _append_if(self, node: ast.If, *, prefix: str, depth: int) -> None:
        self._lines.append(f"{prefix}if {_expr(node.test)}:")
        self._append_block(node.body, depth=depth + 1)
        if node.orelse:
            self._lines.append(f"{prefix}else:")
            self._append_block(node.orelse, depth=depth + 1)

    def _append_exception_or_match(
        self,
        node: ast.AST,
        *,
        prefix: str,
        depth: int,
    ) -> bool:
        if isinstance(node, ast.Try):
            self._lines.append(f"{prefix}try:")
            self._append_block(node.body, depth=depth + 1)
            for handler in node.handlers:
                label = _expr(handler.type) if handler.type is not None else "Exception"
                self._lines.append(f"{prefix}except {label}:")
                self._append_block(handler.body, depth=depth + 1)
            if node.finalbody:
                self._lines.append(f"{prefix}finally:")
                self._append_block(node.finalbody, depth=depth + 1)
            return True
        if isinstance(node, ast.Match):
            self._lines.append(f"{prefix}match {_expr(node.subject)}:")
            for case in node.cases:
                guard = f" if {_expr(case.guard)}" if case.guard is not None else ""
                self._lines.append(f"{prefix}  case {_expr(case.pattern)}{guard}:")
                self._append_block(case.body, depth=depth + 2)
            return True
        return False

    def _append_terminal(
        self,
        node: ast.AST,
        *,
        prefix: str,
        depth: int,
    ) -> bool:
        del depth
        if isinstance(node, ast.Return):
            self._lines.append(f"{prefix}return {_return_expr(node.value)}")
            return True
        if isinstance(node, ast.Raise):
            self._lines.append(f"{prefix}raise {_expr(node.exc)}")
            return True
        if isinstance(node, ast.Break):
            self._lines.append(f"{prefix}break")
            return True
        if isinstance(node, ast.Continue):
            self._lines.append(f"{prefix}continue")
            return True
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await):
            self._lines.append(f"{prefix}await {_expr(node.value.value)}")
            return True
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            self._lines.append(f"{prefix}{_expr(node.value)}")
            return True
        if isinstance(node, ast.Pass):
            self._lines.append(f"{prefix}pass")
            return True
        return False

    def _append_block(
        self,
        body: list[ast.stmt],
        *,
        depth: int,
        max_nodes: int = 24,
    ) -> None:
        for node in body[:max_nodes]:
            self._append_node(node, depth=depth)
        if len(body) > max_nodes:
            self._lines.append(
                f"{'  ' * depth}... {len(body) - max_nodes} more statements"
            )


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _trim_python_line(line: str, base_indent: int) -> str:
    trimmed = line[base_indent:] if len(line) >= base_indent else line
    return trimmed.strip()


def _is_docstring_expr(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _return_expr(node: ast.AST | None) -> str:
    summary = _large_collection_summary(node)
    return summary if summary is not None else _expr(node)


def _large_collection_summary(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.List | ast.Tuple) and len(node.elts) >= 4:
        return _sequence_summary(node)
    if isinstance(node, ast.Dict) and len(node.keys) >= 4:
        return _expr(node)
    return None


def _sequence_summary(node: ast.List | ast.Tuple) -> str:
    labels = _sequence_item_labels(node.elts)
    kind = "list" if isinstance(node, ast.List) else "tuple"
    if not labels:
        return f"{kind}[{len(node.elts)}]"
    shown = ",".join(labels[:6])
    hidden = len(labels) - 6
    suffix = f",...+{hidden}" if hidden > 0 else ""
    return f"{kind}[{len(node.elts)}] items={shown}{suffix}"


def _sequence_item_labels(items: list[ast.expr]) -> list[str]:
    labels: list[str] = []
    for item in items:
        label = _collection_item_label(item)
        if label is not None:
            labels.append(label)
    return labels


def _collection_item_label(node: ast.expr) -> str | None:
    label = _call_item_label(node)
    if label is not None:
        return label
    if isinstance(node, ast.Dict | ast.List | ast.Tuple):
        return _limit_collection_label(_expr(node))
    return None


def _limit_collection_label(label: str, *, max_chars: int = 72) -> str:
    if len(label) <= max_chars:
        return label
    return label[: max_chars - 1].rstrip() + "..."


def _call_item_label(node: ast.expr) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    callee = _expr(node.func)
    if node.args and isinstance(node.args[0], ast.Constant):
        value = node.args[0].value
        if isinstance(value, str):
            return f"{callee}:{value}"
    return callee
