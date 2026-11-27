# Agent Pythonic Policy Research

This note records the evidence behind agent-facing Python readability policy.
The goal is not to replace formatters, linters, type checkers, or pytest. The
goal is to give repair agents a compact reasoning-tree contract for the parts
those tools do not own: algorithm shape, public edit boundaries, and native
Python idioms that keep code small enough for an LLM to edit reliably.

## Target Reader Shift

ASP Python target reader has changed. The primary reader is no longer a human
reviewer looking for pleasant style; it is an Agent or large language model
that must choose a small, correct edit surface from a whole Python project. A
human can tolerate incidental ceremony and remember local context outside the
file. An Agent pays for every repeated branch, every broad loop body, every
untyped data shape, and every ambiguous owner boundary in tokens, attention,
and repair risk.

This changes the policy test. Agent-facing Python quality is the degree to
which parser facts make the project visually navigable for a model before it
edits:

- project anchors: import roots, package branches, public facades, owner maps,
  and internal import edges;
- surface anchors: typed public callables, public data/type/value names,
  explicit exports, and branch intent docstrings;
- data anchors: `dataclass`, `TypedDict`, `Protocol`, `Enum`/`StrEnum`, and
  closed `Literal` domains when parser facts can prove the shape;
- algorithm anchors: guard clauses, `match/case`, dispatch tables,
  comprehensions, generator expressions, built-ins, `collections` helpers, and
  named iterator pipeline steps;
- verification anchors: compact snapshot sections, task contracts, receipts,
  waivers, and responsibility-review tasks.

ASP Python should therefore reject policy ideas that are merely aesthetic. A
new Agent rule needs four properties: it must be backed by parser-owned facts,
it must reduce the model's search or edit surface, it must render as compact
actionable advice rather than redundant explanation, and it must self-apply to
this repository without forcing measured or side-effectful code into a fake
idiom.

## Large Source-Derived Policy Axes

The research sources point to four large axes worth solving before adding more
small lint-like checks:

1. Project navigation anchors. PyPA project metadata, package roots, entry
   points, pytest wiring, exports, owner maps, and internal import edges decide
   where an Agent should edit.
2. Data/type visual anchors. `dataclass`, `TypedDict`, `Protocol`,
   `Enum`/`StrEnum`, `NamedTuple`, `Literal`, and model bases turn implicit
   object shape into a visible contract before the Agent enters a method body.
3. Algorithm intent anchors. `match/case`, comprehensions, generator
   expressions, built-ins, `collections` helpers, iterator tools, and
   `singledispatch` turn broad procedural code into named Python intent.
4. Verification anchors. Pytest gates, profile hints, task contracts,
   receipts, waivers, and report bundles tell an Agent what evidence closes an
   edit.

The implementation should prioritize these axes in that order when choosing
new rules. The first and fourth are already project/reasoning-tree surfaces.
The second is now parser-backed through class-shape facts and `PY-AGENT-POLICY-012`.
The third is covered by `PY-AGENT-POLICY-009` through `PY-AGENT-POLICY-011` and should grow
only when parser facts can prove a native Python replacement.

## Evidence

Official Python guidance gives the north star. PEP 20 names the shape values
directly: explicit code, simple code, flat control flow, sparse structure,
readability, one obvious way, and implementations that are easy to explain.
PEP 8 makes the operational point: code is read much more than written, and
project-local consistency matters more than blind rule application.

Modern Python also has native constructs that remove common LLM boilerplate:

- `match/case` is the language-level pattern matching construct for structured
  branching.
- list comprehensions are documented as the concise way to build mapped or
  filtered lists; the tutorial explicitly contrasts them with an empty list
  plus an append loop.
- `itertools` provides fast, memory efficient iterator building blocks that can
  be composed into compact pure-Python pipelines.
- built-ins such as `any`, `all`, `sum`, `next`, `sorted`, `zip`, `list`,
  `dict`, and `set` make common loop intents explicit.
- `collections.Counter` and `collections.defaultdict` are specialized
  containers for counting and grouping, so agents should not spell those
  algorithms as hand-managed dictionary state.
- `dataclasses` turn plain data carriers into annotated, generated-method data
  models instead of hand-written storage classes.
- `Enum` and `StrEnum` turn closed value sets into named members rather than
  repeated string or integer literals.
- `typing.Protocol`, `TypedDict`, and `Literal` make structural interfaces,
  dictionary payloads, and closed literal domains visible to tools and agents.
- `functools.singledispatch` provides a standard-library dispatch surface for
  type-directed behavior that would otherwise become a broad `isinstance`
  ladder.
- `typing` is not runtime enforcement, but it gives tools and agents explicit
  callable and data shapes.

GitHub practice shows the adjacent tool baseline. Current mature Python repos
such as `pydantic/pydantic`, `pytest-dev/pytest`, `encode/httpx`, and
`psf/black` centralize project metadata in `pyproject.toml` and commonly wire
pytest, ruff, mypy, or pyright. That means ASP Python should not duplicate
style or type-check rules. Its useful scope is the parser-backed project and
algorithm contract that an LLM sees before it edits code.

## ASP Python Thesis

ASP Python should classify Python quality in three layers:

1. Tool substrate: packaging metadata, pytest gate, ruff, and type-checker
   configuration. Parser facts expose this layer, but normal tools enforce it.
2. Project reasoning tree: packages, public facades, owner maps, imports, and
   public callable/type/value boundaries. This is where an agent chooses where
   to edit.
3. Algorithm readability for agents: public functions should expose a small
   algorithm surface through guard clauses, native dispatch, comprehensions,
   iterator tools, built-ins, and named pipeline steps.

The third layer is where policy adds value. LLMs often spell Python as generic
pseudocode: nested `if`/`else`, broad loops, empty accumulator containers,
boolean flags, and manual search loops. Python has native idioms for many of
these shapes. A parser-backed advisory rule can point agents toward those
idioms without blocking valid explicit loops.

The long-term shape is a visual reasoning tree, not a pile of style
diagnostics. The tree should let an Agent see: which package owns the change,
which public surface is affected, which data shapes and closed domains govern
the function, which algorithm step is map/filter/count/group/sum/dispatch, and
which verification task proves the edit. That is the basis for short, native
Python code that is also easier for a model to repair.

## Rule Direction

Existing rules cover two algorithm-shape problems:

- `PY-AGENT-POLICY-009`: nested control flow and literal dispatch ladders.
- `PY-AGENT-POLICY-010`: broad linear public functions.

The next policy step is not another size threshold. It is native-idiom advice:
when the parser sees a simple module-level function or public method manually
building a list, set, or dict in a loop, manually counting/grouping into a
dictionary, manually summing numeric values, or returning a boolean through a
trivial predicate loop, ASP Python should ask the agent to use a comprehension,
generator expression, built-in such as `sum`/`any`/`all`,
`collections.Counter`, `collections.defaultdict`, or named iterator pipeline.
This is advisory because explicit loops remain correct for side effects,
complex state machines, debugging, or performance-sensitive code that has been
measured.

## Candidate Matrix

| Candidate | Evidence | ASP Python action |
| --- | --- | --- |
| Map/filter/list/set/dict build loops | Python Functional HOWTO on comprehensions and generator expressions | Implemented by parser fact `manual_collection_loop_count` |
| Predicate search loops | Python built-ins and Functional HOWTO predicate guidance | Implemented by parser fact `manual_predicate_loop_count` |
| Dictionary counting/grouping loops | `collections.Counter` and `defaultdict` official docs; pytest and pydantic use both in project code | Implement as parser facts for manual counter/grouping loops |
| Numeric accumulation loops | Built-in `sum` and generator expression guidance | Implement as parser fact for simple `total += expr` loops |
| Data carrier classes | `dataclasses` official docs | Implemented by parser-owned class-shape facts and `PY-AGENT-POLICY-012` |
| Closed state/value sets | `enum.Enum`, `enum.StrEnum`, and `typing.Literal` official docs | Research-only for now; needs parser facts for repeated literal domains and existing enum surfaces |
| Structural interfaces | `typing.Protocol` official docs | Research-only for now; parser already exposes base classes, but policy needs role/use facts before advice |
| Dictionary payload shapes | `typing.TypedDict` official docs | Research-only for now; needs parser facts for repeated dict-literal key sets and public payload boundaries |
| Resource lifetime / context managers | `contextlib` and `pathlib` docs, plus existing Ruff coverage | Defer to tool substrate unless parser can prove unsafe lifetime |
| Type dispatch | `match/case` and `functools.singledispatch` docs | Covered partly by `PY-AGENT-POLICY-009`; enrich later only with concrete parser facts |

## Sources

- https://peps.python.org/pep-0020/
- https://peps.python.org/pep-0008/
- https://docs.python.org/3/reference/compound_stmts.html#the-match-statement
- https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
- https://docs.python.org/3/library/itertools.html
- https://docs.python.org/3/library/functions.html
- https://docs.python.org/3/library/collections.html
- https://docs.python.org/3/library/dataclasses.html
- https://docs.python.org/3/library/enum.html
- https://docs.python.org/3/library/typing.html
- https://docs.python.org/3/library/functools.html
- https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- https://github.com/pydantic/pydantic
- https://github.com/pytest-dev/pytest
- https://github.com/encode/httpx
- https://github.com/psf/black
