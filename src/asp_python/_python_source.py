"""Source slicing helpers for Python compact AST projection."""

from __future__ import annotations

import ast


def parse_python_lines(raw_lines: list[str]) -> ast.Module | None:
    source = dedented_python_source(raw_lines)
    if source is None:
        return None
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def dedented_python_source(raw_lines: list[str]) -> str | None:
    selected = [line.rstrip() for line in raw_lines if line.strip()]
    if not selected:
        return None
    base_indent = min(_leading_spaces(line) for line in selected)
    return "\n".join(
        line[base_indent:] if len(line) >= base_indent else line for line in raw_lines
    )


def fallback_compact_code(raw_lines: list[str]) -> str:
    selected = [line.rstrip() for line in raw_lines if line.strip()]
    if not selected:
        return ""
    base_indent = min(_leading_spaces(line) for line in selected)
    return "\n".join(_trim_python_line(line, base_indent) for line in selected)


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _trim_python_line(line: str, base_indent: int) -> str:
    trimmed = line[base_indent:] if len(line) >= base_indent else line
    return trimmed.strip()
