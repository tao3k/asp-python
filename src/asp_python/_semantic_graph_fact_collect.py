"""Collect Python field/type facts from parser-owned AST."""

from __future__ import annotations

import ast
from pathlib import Path

from ._semantic_graph_fact_model import FieldFact, collection_kind

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "venv",
    ".venv",
}


def collect_field_facts(project_root: Path, query: str, stdin: str) -> list[FieldFact]:
    terms = query_terms(query)
    paths = candidate_paths(project_root, stdin) or python_source_paths(project_root)
    facts: list[FieldFact] = []
    seen: set[tuple[str, str, str, int]] = set()
    for path in paths:
        for fact in field_facts_for_path(project_root, path):
            key = (fact.path, fact.container_name, fact.field_name, fact.line)
            if key in seen or not fact_matches_terms(fact, terms):
                continue
            seen.add(key)
            facts.append(fact)
            if len(facts) >= 64:
                return facts
    return facts


def candidate_paths(project_root: Path, stdin: str) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for line in stdin.splitlines():
        path_text = line.split(":", 1)[0].strip()
        if not path_text:
            continue
        path = Path(path_text)
        absolute = path if path.is_absolute() else project_root / path
        if absolute.suffix != ".py" or not absolute.exists() or absolute in seen:
            continue
        seen.add(absolute)
        paths.append(absolute)
    return paths


def python_source_paths(project_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in project_root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(project_root).parts):
            continue
        paths.append(path)
    return sorted(paths)


def field_facts_for_path(project_root: Path, path: Path) -> list[FieldFact]:
    try:
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    relative_path = path.relative_to(project_root).as_posix()
    facts: list[FieldFact] = []
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef):
            facts.extend(class_field_facts(relative_path, node))
    return facts


def class_field_facts(path: str, class_node: ast.ClassDef) -> list[FieldFact]:
    facts: list[FieldFact] = []
    for item in class_node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            type_value = annotation_text(item.annotation)
            if type_value is not None:
                facts.append(
                    field_fact(
                        path,
                        class_node.name,
                        item.target.id,
                        type_value,
                        item.lineno,
                        class_node.lineno,
                        getattr(class_node, "end_lineno", item.lineno),
                    )
                )
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            facts.extend(init_self_field_facts(path, class_node, item))
    return facts


def init_self_field_facts(
    path: str,
    class_node: ast.ClassDef,
    init_node: ast.FunctionDef,
) -> list[FieldFact]:
    facts: list[FieldFact] = []
    for item in ast.walk(init_node):
        if isinstance(item, ast.AnnAssign):
            fact = self_field_fact(path, class_node, init_node, item)
            if fact is not None:
                facts.append(fact)
    return facts


def self_field_fact(
    path: str,
    class_node: ast.ClassDef,
    init_node: ast.FunctionDef,
    item: ast.AnnAssign,
) -> FieldFact | None:
    target = item.target
    if not (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ):
        return None
    type_value = annotation_text(item.annotation)
    if type_value is None:
        return None
    return field_fact(
        path,
        class_node.name,
        target.attr,
        type_value,
        item.lineno,
        init_node.lineno,
        getattr(init_node, "end_lineno", item.lineno),
    )


def field_fact(
    path: str,
    container_name: str,
    field_name: str,
    type_value: str,
    line: int,
    context_start: int,
    context_end: int,
) -> FieldFact:
    return FieldFact(
        path=path,
        container_name=container_name,
        field_name=field_name,
        type_value=type_value,
        collection_kind=collection_kind(type_value),
        line=line,
        context_start=context_start,
        context_end=context_end,
    )


def annotation_text(annotation: ast.expr) -> str | None:
    try:
        return ast.unparse(annotation)
    except (AttributeError, ValueError):
        return None


def query_terms(query: str) -> set[str]:
    normalized = "".join(
        character.lower() if character == "_" or character.isalnum() else " "
        for character in query
    )
    return {term for term in normalized.split() if term}


def fact_matches_terms(fact: FieldFact, terms: set[str]) -> bool:
    if not terms or terms & semantic_shape_terms():
        return True
    text = " ".join(
        part
        for part in (
            fact.container_name,
            fact.field_name,
            fact.type_value,
            fact.collection_kind or "",
        )
        if part
    ).lower()
    return any(term in text for term in terms)


def semantic_shape_terms() -> set[str]:
    return {
        "field",
        "fields",
        "type",
        "types",
        "scalar",
        "scalars",
        "collection",
        "collections",
        "list",
        "lists",
        "map",
        "maps",
        "set",
        "sets",
        "dict",
        "tuple",
    }
