# Rule Catalog

:PROPERTIES:
:ID: 4af1b8e663ad854b94d6bd438596ab03c9829653
:TYPE: FEATURE
:STATUS: ACTIVE
:LAST_SYNC: 2026-05-05
:END:

The harness exposes deterministic rule metadata through compact library
functions:

- `python_rule_pack_descriptors()`
- `python_syntax_rules()`
- `python_modern_design_rules()`
- `python_project_policy_rules()`
- `python_agent_policy_rules()`
- `python_modularity_rules()`
- `python_test_layout_rules()`

## Default Rule Packs

Default project execution runs these packs:

1. `python.syntax`
2. `python.project_policy`
3. `python.modern_design`
4. `python.modularity`
5. `python.test_layout`
6. `python.agent_policy`

`python.agent_policy` is advisory by default and runs after the blocking packs.
Most other default-pack findings block through `Warning` or `Error`; project
policy can also emit `Info` configuration work orders for Agents.

## Blocking Rules

- `python.syntax.invalid`: Python source must parse through CPython-native
  syntax.
- `python.compile.invalid`: Python source must compile through CPython-native
  validation.
- `PY-AGENT-PROJECT-001`: Python projects should use `src/` layout.
- `PY-AGENT-PROJECT-002`: declared wheel package roots must be importable packages.
- `PY-AGENT-PROJECT-003`: public typed package roots should include `py.typed`.
- `PY-AGENT-PROJECT-004`: public callable boundaries in typed packages need
  annotations.
- `PY-AGENT-PROJECT-005`: `[project]` metadata should declare package name.
- `PY-AGENT-PROJECT-006`: `[project]` metadata should declare supported Python
  versions.
- `PY-AGENT-PROJECT-007`: `[build-system]` tables should declare build requirements.
- `PY-AGENT-PROJECT-008`: `[project].import-names` and `import-namespaces` should
  resolve to parser-visible project module owners.
- `PY-AGENT-PROJECT-009`: console script, GUI script, and entry point targets should
  resolve to parser-visible project modules.
- `PY-AGENT-PROJECT-010`: projects that declare the harness as a test/dev dependency
  should mount a parser-visible pytest gate.
- `PY-MOD-R001`: wildcard imports must become explicit imports.
- `PY-MOD-R002`: library modules should not use bare `print`.
- `PY-MOD-R003`: package facades with re-exports should declare `__all__`.
- `PY-MOD-R004`: library modules should not contain `breakpoint()`.
- `PY-MOD-R006`: large multi-responsibility modules should split behind a
  focused package facade.
- `PY-MOD-R007`: one Python import namespace should have one source owner,
  avoiding `module.py` plus `module/__init__.py` reasoning-tree shadows.
- `PY-TEST-R001`: pytest modules should not be scattered in the tests root.
- `PY-TEST-R002`: tests root entries should be owned suite directories or
  harness configuration files.
- `PY-TEST-R003`: large unit-test leaves should split into folder-first suites.

Project-local pytest-layout exceptions live in
`tests/python-project-harness-rules.toml`; each exception needs a non-empty
explanation before it suppresses `PY-TEST-*` findings.

`PY-MOD-R006` is a mixed-signal modularity gate, not a line-count gate. The
rule first requires the parser-owned effective-line budget to be exceeded, then
requires either a long function span or multiple split indicators such as many
top-level items, mixed responsibility groups, or a wide public surface. Large
single-signal modules, such as generated constants or narrow data tables, do
not fail only because they are long.

## Project Advice Rules

Some project-policy findings are intentionally `Info`: they are configuration
work orders for the repair Agent, not immediate merge blockers.

- `PY-AGENT-PROJECT-011`: projects that declare the harness as a test/dev dependency
  and expose parser-visible verification owners should configure
  `[tool.python-lang-project-harness.verification].profile_hints`. The finding
  points the Agent to `asp-python --agent-snapshot`, whose compact
  `[verify-profile]` section is the config draft.

## Agent Advice Rules

`PY-AGENT-*` rules are `Info` findings. They are designed as repair hints for
LLMs and are not blocking by default.

The target reader for these rules is the repair Agent, not a human style
reviewer. A rule belongs in this pack only when parser-owned facts expose a
shape that makes the project harder for a model to navigate or edit: ambiguous
ownership, unclear public surface, broad algorithm bodies, nested control flow,
or hand-written loops that hide a native Python intent. The advice should make
the reasoning tree more visually legible to an Agent while staying compact
enough to use as the first repair prompt.

- `PY-AGENT-POLICY-001`: public module surface lacks an intent docstring.
- `PY-AGENT-POLICY-002`: public callable lacks type annotations.
- `PY-AGENT-POLICY-003`: public callable name conflicts across namespaces.
- `PY-AGENT-POLICY-004`: module namespace repeats a path segment.
- `PY-AGENT-POLICY-005`: public type name conflicts across namespaces.
- `PY-AGENT-POLICY-006`: public value name conflicts across namespaces.
- `PY-AGENT-POLICY-007`: branch packages with multiple child modules should include
  a reasoning-tree intent docstring.
- `PY-AGENT-POLICY-008`: broad branch packages should split into focused subpackages
  or document the facade and owner map for agent repair loops.
- `PY-AGENT-POLICY-009`: top-level functions and public methods with deeply nested
  control flow should
  expose the algorithm shape through guard clauses, explicit dispatch,
  `match/case`, or small named pipeline steps.
- `PY-AGENT-POLICY-010`: top-level functions and public methods with broad linear
  statement blocks should split into named helpers or pipeline steps that are
  easier for agents to edit.
- `PY-AGENT-POLICY-011`: top-level functions and public methods that manually spell
  simple collection or predicate loops should use native Python idioms such as
  comprehensions, generator expressions, built-ins such as `sum`/`any`/`all`,
  `collections.Counter`/`defaultdict`, or named iterator pipeline helpers.
- `PY-AGENT-POLICY-012`: public classes that mainly store instance fields in
  `__init__` should expose a visible data/type anchor such as `dataclass`,
  `TypedDict`, `Protocol`, `Enum`/`StrEnum`, or a named model base.

## Reasoning Tree Policy

The harness treats a Python project as an agent reasoning tree: import roots
lead to package branches, package branches lead to modules, and modules expose
the parser-owned public surface. `python_lang_parser` owns the tree facts:
tree nodes, child names, public/internal surface flags, module/package owner
shadows, internal import edges, and branch package child counts are derived
from `PythonModuleReport` paths, parser import records, module shape,
public-surface helpers, export candidates, `__all__` contract kind, module
docstrings, and parser-owned `pyproject.toml` metadata.

`PY-MOD-R007` blocks a collapsed owner tree such as `domain.py` next to
`domain/__init__.py`, because both spell the same import owner and repair
agents cannot know which surface owns the change. `PY-AGENT-POLICY-007` stays
advisory and asks branch package `__init__.py` files with multiple child
modules to carry a short intent docstring, so agents can choose the right
subtree before editing. `PY-AGENT-POLICY-008` is also advisory; it combines branch
child count with public-child and effective-line signals so crowded non-facade
folders surface as owner-map advice without becoming a raw child-count gate.
Packages that already expose an explicit public facade are treated as having
an owner map.

`PY-AGENT-POLICY-009` is backed by parser-owned function control-flow facts, not by
harness string scanning. The parser records branch count, loop count, maximum
nesting, loop nesting, terminal `else` opportunities, and repeated literal
dispatch chains for each function symbol during the normal AST collection pass.
The harness turns those facts into a compact repair hint when a public function
hides its algorithm behind nested `if`/loop structure. The rule stays advisory
by default so teams can tune or promote it after seeing their project shape.

The implementation lives under `python_lang_project_harness.agent_readability`
because the target reader is the repair agent, not a human style reviewer. The
goal is short, explicit algorithm surfaces that an LLM can use from the
reasoning tree: guard clauses instead of nested `else`, `match/case` or dispatch
tables instead of literal branch ladders, and small named pipeline steps instead
of one broad loop body. Performance remains parser-first: the harness only
consumes `PythonFunctionControlFlow` facts and does not run a second AST parse.
`PY-AGENT-POLICY-010` complements `PY-AGENT-POLICY-009`: the former catches long flat
procedure-like public functions, while the latter catches nested control-flow
shape. This keeps the advice compact and avoids telling the agent the same
thing twice.

`PY-AGENT-POLICY-011` is the native-Python idiom layer. It is backed by parser-owned
function facts for simple accumulator loops and predicate loops, so the harness
can advise comprehensions, generator expressions, built-ins, or iterator
pipeline helpers without parsing source in the policy layer. The rule is
conservative: it targets module-level functions and public methods where a loop
only maps, filters, counts, groups, accumulates, or answers a boolean predicate.
Explicit loops remain valid for effects, complex state machines, debugging, or
measured performance work.

`PY-AGENT-POLICY-012` is the data/type visual-anchor layer. It is backed by
parser-owned class-shape facts: annotated class fields, `__init__` self-field
storage, method counts, and visible anchors such as `dataclass`, `Enum`,
`StrEnum`, `Protocol`, `TypedDict`, `NamedTuple`, or a named model base. The
rule stays advisory and only targets public classes that mostly hand-store
fields without public behavior. The goal is to make data shapes visible before
an Agent opens the function body, not to ban ordinary service objects.

`render_python_reasoning_tree()` exposes the same tree as compact text for LLM
repair loops. It includes an `[imports]` section for parser-resolved
project-internal edges, a compact `[project]` section for declared package
metadata and entry targets, and compact `exports=` flags on public nodes,
making it the preferred first read when an agent needs to understand where a
change belongs, what public API it touches, and what it may affect before
touching code. In project-scoped reports, paths render relative to the project
root so the tree does not repeat long absolute prefixes.

## Rendered Diagnostic Policy

Rendered findings intentionally avoid large JSON payloads. The primary repair
surface is compact text:

1. stable rule id
2. source location
3. highlighted source line when available
4. short pointer label
5. one precise `Required:` contract line

Non-clean compact output is finding-first: it does not prepend a file-count or
issue-count header before the first blocking finding. Advice-only output starts
with `[advice]` and then concrete findings; it does not prepend an `[ok]`
summary or issue-count line. Clean output keeps only a short `[ok]` line plus
the file/parsed count needed for CI confidence. In project-scoped reports,
compact text renders paths relative to the project root; JSON keeps the
structured original paths for tooling.

`render_python_lang_harness()` includes advice by default. A report with only
`Info` findings is still clean, but its advice remains visible without
run-summary noise. Use
`render_python_lang_harness_advice()` when a caller wants only non-blocking
repair hints; it returns an empty string when there is no advice to act on.

Structured consumers should use `render_python_lang_harness_json()` or the
`PythonHarnessReport.to_dict()` shape instead of parsing compact text.

## Parser-First Policy

Python semantic policy is parser-first. Rule packs consume
`PythonModuleReport` facts instead of opening Python files and guessing from raw
text. `python_lang_parser` owns AST, compile, tokenize, symbol-table, source
line, module-shape, public-name, public-surface, symbol-role, and import-root
module identity facts, standard `pyproject.toml` project metadata, and package
reasoning-tree facts.
`python_lang_project_harness` owns rule catalogs, project/test layout,
reporting, and assertion behavior.

Repository tests enforce this boundary by rejecting direct `ast` or `tokenize`
usage under `src/python_lang_project_harness`. File and metadata checks may
still read non-Python policy inputs such as
`python-project-harness-rules.toml`; Python project metadata should flow
through parser-owned `pyproject.toml` facts.

## Snapshot Coverage

The compact text and JSON render contracts are covered by repository snapshots
under `tests/unit/snapshots`:

- `python_project_harness_compact_text.snap`
- `python_project_harness_json.snap`

Policy snapshots are generated from real harness fixtures and normalized to
`$TEMP` paths. Every current `PY-AGENT-*` rule has a compact advice snapshot.
The blocking policy surface also has snapshots for native syntax,
`PY-MOD-*`, `PY-PROJ-*`, and `PY-TEST-*` findings. This keeps rule titles,
pointer labels, source snippets, and `Required:` contracts reviewable as
ordinary snapshot diffs.

Refresh snapshots explicitly:

```shell
PYTHON_HARNESS_UPDATE_SNAPSHOTS=1 direnv exec . uv run --group test pytest \
  tests/unit/harness/test_render_snapshots.py \
  tests/unit/harness/test_agent_policy_snapshots.py \
  tests/unit/harness/test_policy_snapshots.py -q
```

:RELATIONS:
:LINKS: [Harness Boundary](../01_core/101_harness_boundary.md)
:END:
