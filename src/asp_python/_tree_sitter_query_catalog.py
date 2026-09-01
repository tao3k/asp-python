"""Provider-embedded Python tree-sitter query catalog metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._tree_sitter_query_model import PythonTreeSitterCatalog

PYTHON_TREE_SITTER_GRAMMAR_ID = "tree-sitter-python"
PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION = "2026-06-04.v1"
PYTHON_TREE_SITTER_GRAMMAR_PROFILE_PATH = (
    "tree-sitter/tree-sitter-python/grammar-profile.json"
)

CATALOGS = {
    "declarations": PythonTreeSitterCatalog(
        id="declarations",
        path="tree-sitter/tree-sitter-python/queries/declarations.scm",
        captures=(
            "function.definition",
            "function.name",
            "class.definition",
            "class.name",
        ),
        source=""";; Python declaration captures projected from native ast facts.

(function_definition
  name: (identifier) @function.name) @function.definition

(class_definition
  name: (identifier) @class.name) @class.definition
""",
    ),
    "imports": PythonTreeSitterCatalog(
        id="imports",
        path="tree-sitter/tree-sitter-python/queries/imports.scm",
        captures=("import.declaration", "import.name", "import.path", "import.alias"),
        source=""";; Python import binding captures projected from ast.Import and ast.ImportFrom.

(import_statement
  name: (dotted_name) @import.name) @import.declaration

(import_from_statement
  module_name: (dotted_name)? @import.path
  name: (dotted_name) @import.name) @import.declaration

(aliased_import
  name: (dotted_name) @import.name
  alias: (identifier) @import.alias)
""",
    ),
    "calls": PythonTreeSitterCatalog(
        id="calls",
        path="tree-sitter/tree-sitter-python/queries/calls.scm",
        captures=("call.expression", "call.target", "call.method", "call.keyword"),
        source=""";; Python call target captures projected from ast.Call.

(call
  function: (_) @call.target) @call.expression

(call
  function: (attribute
    attribute: (identifier) @call.method)) @call.expression

(keyword_argument
  name: (identifier) @call.keyword)
""",
    ),
    "decorators": PythonTreeSitterCatalog(
        id="decorators",
        path="tree-sitter/tree-sitter-python/queries/decorators.scm",
        captures=("decorator.expression", "decorator.target", "decorator.call"),
        source=""";; Python decorator captures projected from decorated ast definitions.

(decorated_definition
  (decorator) @decorator.expression
  definition: (_) @decorator.target)

(decorator
  (call
    function: (_) @decorator.call))
""",
    ),
    "control-flow": PythonTreeSitterCatalog(
        id="control-flow",
        path="tree-sitter/tree-sitter-python/queries/control-flow.scm",
        captures=(
            "control.if",
            "control.condition",
            "control.loop",
            "control.target",
            "control.iterable",
            "control.with",
            "context.manager",
            "control.exception",
            "control.match",
            "control.subject",
        ),
        source=""";; Python control-flow captures projected from native ast statements.

(if_statement
  condition: (_) @control.condition) @control.if

(for_statement
  left: (_) @control.target
  right: (_) @control.iterable) @control.loop

(while_statement
  condition: (_) @control.condition) @control.loop

(with_statement
  (with_item) @context.manager) @control.with

(try_statement) @control.exception

(match_statement
  subject: (_) @control.subject) @control.match
""",
    ),
}


CATALOG_NODE_TYPES: dict[str, tuple[str, ...]] = {
    "declarations": ("function_definition", "class_definition"),
    "imports": ("import_statement", "import_from_statement", "aliased_import"),
    "calls": ("call", "attribute", "keyword_argument"),
    "decorators": ("decorated_definition", "decorator", "call"),
    "control-flow": (
        "if_statement",
        "for_statement",
        "while_statement",
        "with_statement",
        "try_statement",
        "match_statement",
        "with_item",
    ),
}

CATALOG_FIELDS: dict[str, tuple[str, ...]] = {
    "declarations": ("name",),
    "imports": ("alias", "module_name", "name"),
    "calls": ("attribute", "function", "name"),
    "decorators": ("definition", "function"),
    "control-flow": ("condition", "left", "right", "subject"),
}


def python_tree_sitter_query_catalog_descriptors() -> list[dict[str, Any]]:
    return [
        {
            "id": catalog.id,
            "path": catalog.path,
            "captures": list(catalog.captures),
            "nodeTypes": list(CATALOG_NODE_TYPES[catalog.id]),
            "fields": list(CATALOG_FIELDS[catalog.id]),
            "sourceDelivery": "provider-binary-embedded",
        }
        for catalog in CATALOGS.values()
    ]


def resolved_tree_sitter_query(args: Any) -> dict[str, Any]:
    if args.catalog is not None and args.tree_sitter_query is not None:
        raise ValueError("query accepts only one of --catalog or --treesitter-query")
    if args.catalog is not None:
        catalog = CATALOGS.get(args.catalog)
        if catalog is None:
            raise ValueError(
                f"unknown Python tree-sitter query catalog: {args.catalog}"
            )
        return {
            "input": catalog.id,
            "inputForm": "catalog-id",
            "catalogId": catalog.id,
            "catalogPath": catalog.path,
            "source": catalog.source,
            "captures": catalog.captures,
            "nodeTypes": CATALOG_NODE_TYPES[catalog.id],
            "fields": CATALOG_FIELDS[catalog.id],
            "predicates": (),
            "catalogCanonical": True,
            "catalogEmbedded": True,
        }
    if args.tree_sitter_query is None or not args.tree_sitter_query.strip():
        raise ValueError("missing --catalog or --treesitter-query value")
    source = args.tree_sitter_query.strip()
    if not args.asp_syntax_query_node_types:
        raise ValueError(
            "tree-sitter query projection requires ASP-compiled query plan; use "
            "`asp python query --treesitter-query ...` so ASP owns query ABI compilation"
        )
    return {
        "input": source,
        "inputForm": "s-expression",
        "catalogId": None,
        "catalogPath": None,
        "source": source,
        "captures": tuple(args.asp_syntax_query_captures),
        "nodeTypes": tuple(args.asp_syntax_query_node_types),
        "fields": tuple(args.asp_syntax_query_fields),
        "predicates": tuple(args.asp_syntax_query_predicates),
        "catalogCanonical": False,
        "catalogEmbedded": False,
    }


def grammar_profile_source() -> str:
    root = Path(__file__).resolve().parents[2]
    profile_path = root / PYTHON_TREE_SITTER_GRAMMAR_PROFILE_PATH
    try:
        return profile_path.read_text(encoding="utf-8")
    except OSError:
        return json.dumps(
            {
                "grammarId": PYTHON_TREE_SITTER_GRAMMAR_ID,
                "grammarProfileVersion": PYTHON_TREE_SITTER_GRAMMAR_PROFILE_VERSION,
                "catalogs": python_tree_sitter_query_catalog_descriptors(),
            },
            sort_keys=True,
        )
