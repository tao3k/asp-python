"""Provider-owned fact catalog for Python language knowledge axes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

AxisDetail = dict[str, str]
KnowledgeFact = dict[str, Any]

_AXIS_DETAILS: dict[str, AxisDetail] = {
    "env": {
        "authority": "project-environment",
        "summary": "Python environment facts from pyproject, package metadata, and import roots.",
        "next": "search lang import packaging",
    },
    "runtime-source": {
        "authority": "local-source",
        "summary": "Python provider has no runtime checkout resolver; use owner/query/deps evidence.",
        "next": "search deps <package>",
    },
    "lang": {
        "authority": "language-rules",
        "summary": "Python syntax and runtime semantics visible to ast/tokenize/symtable facts.",
        "next": "query guide treesitter",
    },
    "std": {
        "authority": "standard-library",
        "summary": "Python standard-library API and idiom facts for agent code generation.",
        "next": "search api <symbol>",
    },
    "capability": {
        "authority": "provider-registry",
        "summary": "Python provider method and capability registry facts.",
        "next": "guide",
    },
    "extension": {
        "authority": "ecosystem-extension",
        "summary": "Framework or package-specific Python ecosystem extension evidence.",
        "next": "search deps <package>",
    },
    "pattern": {
        "authority": "executable-pattern",
        "summary": "Executable syntax and API patterns backed by owner/deps/tree-sitter evidence.",
        "next": "search owner <path> items --query <symbol>",
    },
    "compare": {
        "authority": "semantic-comparison",
        "summary": "Compare Python project, dependency, or syntax axes using provider-owned facts.",
        "next": "run each side through matching provider axis",
    },
}

_LANG_FACTS = [
    ("module-import", {"syntax": "import/from", "selector": "query --catalog imports"}),
    ("decorator", {"syntax": "@decorator", "selector": "query --catalog declarations"}),
    ("class-protocol", {"syntax": "class/Protocol", "selector": "search api Protocol"}),
]

_STD_FACTS = [
    ("pathlib", {"symbol": "pathlib.Path", "pattern": "filesystem path API"}),
    ("dataclasses", {"symbol": "dataclasses.dataclass", "pattern": "record modeling"}),
    ("typing", {"symbol": "typing", "pattern": "type contracts and protocols"}),
    ("itertools", {"symbol": "itertools", "pattern": "iterator composition"}),
]

_CAPABILITY_FACTS = [
    ("owner-items", {"command": "search owner <path> items"}),
    ("deps", {"command": "search deps <pkg[@ver][::api]>"}),
    ("tree-sitter", {"command": "query --treesitter-query <pattern>"}),
]

_PATTERN_FACTS = [
    (
        "declaration-to-owner-query",
        {
            "command": "query --catalog declarations then search owner <path> items",
            "qualitySignal": "parser-owned declaration before code read",
        },
    ),
    (
        "dependency-api-usage",
        {
            "command": "search deps <dependency>::<api>",
            "qualitySignal": "dependency and local usage evidence",
        },
    ),
]


def axis_detail(axis: str) -> AxisDetail:
    """Return stable packet metadata for a provider knowledge axis."""

    return _AXIS_DETAILS.get(axis, _AXIS_DETAILS["capability"])


def knowledge_facts(
    project_root: Path, axis: str, terms: list[str]
) -> list[KnowledgeFact]:
    """Return provider-owned facts for the requested axis."""

    if axis == "env":
        return _env_facts(project_root, terms)
    if axis == "runtime-source":
        return []
    if axis == "extension":
        return _extension_facts(project_root, terms)
    if axis == "compare":
        return _compare_facts(axis, terms)
    return _filter_facts(_static_axis_facts(axis), terms)


def _static_axis_facts(axis: str) -> list[KnowledgeFact]:
    if axis == "lang":
        return _facts(axis, _LANG_FACTS)
    if axis == "std":
        return _facts(axis, _STD_FACTS)
    if axis == "capability":
        return _facts(axis, _CAPABILITY_FACTS)
    if axis == "pattern":
        return _facts(axis, _PATTERN_FACTS)
    return []


def _env_facts(project_root: Path, terms: list[str]) -> list[KnowledgeFact]:
    candidates = (project_root / "pyproject.toml", project_root / "setup.cfg")
    facts = [
        _fact(
            path.name,
            "env",
            path=str(path.relative_to(project_root)),
            source="project-config",
        )
        for path in candidates
        if path.exists()
    ]
    return _filter_facts(facts, terms)


def _extension_facts(project_root: Path, terms: list[str]) -> list[KnowledgeFact]:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return []
    text = pyproject.read_text(encoding="utf-8", errors="replace")
    return [
        _fact("pyproject", "extension", source="pyproject.toml", match=term)
        for term in terms
        if term and term in text.lower()
    ]


def _compare_facts(axis: str, terms: list[str]) -> list[KnowledgeFact]:
    return [
        _fact(
            "compare-query",
            axis,
            left=terms[0] if len(terms) > 0 else "-",
            right=terms[1] if len(terms) > 1 else "-",
            route="run each side through the matching provider axis and compare facts",
        )
    ]


def _facts(axis: str, rows: list[tuple[str, dict[str, str]]]) -> list[KnowledgeFact]:
    return [_fact(fact_id, axis, **fields) for fact_id, fields in rows]


def _fact(fact_id: str, axis: str, **fields: str) -> KnowledgeFact:
    return {"id": fact_id, "fields": {"axis": axis, **fields}}


def _filter_facts(facts: list[KnowledgeFact], terms: list[str]) -> list[KnowledgeFact]:
    if not terms:
        return facts
    return [fact for fact in facts if _matches_terms(str(fact), terms)]


def _matches_terms(value: str, terms: list[str]) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in terms)
