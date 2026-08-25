# Harness Boundary

:PROPERTIES:
:ID: 5fa0fe2dac2c4668b1ad949a8590d0098679cb1b
:TYPE: CORE
:STATUS: ACTIVE
:LAST_SYNC: 2026-04-30
:END:

`python-lang-project-harness` owns a standalone, library-first Python project
harness. It keeps parser facts and project policy in separate import packages,
but ships them from the same repo so downstream users do not depend on the old
monorepo workspace layout.

## Ownership

This repository may:

1. parse Python modules through Python-native standard-library surfaces
2. discover whole-project Python files with conventional roots as
   classification inputs
3. evaluate deterministic rule packs over parser reports and project scope
4. render compact diagnostics for humans and repair-oriented agents
5. expose structured reports and JSON rendering for tooling
6. expose pytest-friendly assertion helpers and collectable harness callables
7. expose a thin CLI over the default project runner

This repository must not own:

1. Python runtime orchestration
2. workflow execution
3. routing, memory, indexing, or transport
4. CI-provider-specific policy
5. project-specific allowlists hidden inside the library
6. long-running daemon behavior

## Parser Boundary

`python_lang_parser` owns Python-native facts. It uses `ast`, `compile`,
`tokenize`, and `symtable` rather than `tree-sitter`. It emits compact module
reports with imports, symbols, scopes, bindings, references, calls,
assignments, export contracts, shape summaries, and diagnostics.
It also parses standard `pyproject.toml` project metadata such as
`[project].name`, `requires-python`, `import-names`, scripts, entry points,
build-system requirements, and declared package roots.
For class surfaces it owns data/type shape facts such as annotated class
fields, `__init__` self-field storage, method counts, and visible anchors like
`dataclass`, `Enum`, `Protocol`, `TypedDict`, `NamedTuple`, or model bases.

`python_lang_project_harness` consumes those reports. It owns rule
catalogs, project discovery, report aggregation, rendering, and pytest
embedding. Rule packs should depend on parser facts rather than ad hoc source
text matching when a structured fact exists.

Parser-backed policy is the default architectural rule. Python semantic checks
must not re-parse source inside the harness layer; they should use
`PythonModuleReport` facts such as imports, calls, symbols, assignments, export
contracts, source lines, and module shape. Standard Python project metadata
should flow through parser-owned `pyproject.toml` facts. Harness-owned policy
inputs such as tests-root policy TOML may still be read in the harness layer,
but they must not infer Python semantics from raw text.

`PY-TEST-R003` follows the same boundary: unit-test bloat is calculated from
parser-owned module shape and parser-classified test symbols. The harness owns
the pytest layout contract, while `python_lang_parser` owns Python syntax,
tokenization, AST, compile validation, source-line capture, public-name policy,
module public-surface classification, symbol-role classification, and
import-root module identity helpers. It also owns `pyproject.toml` metadata
facts used by project policy and reasoning-tree renderers.

Reasoning-tree policy follows that boundary as well. `python_lang_parser`
derives package tree facts from parsed module reports: import-owner shadows
such as `domain.py` beside `domain/__init__.py`, and branch packages whose
immediate child modules need an intent docstring for agent navigation. It also
resolves project-internal import edges from parser import records and import
roots, so agents can see which modules depend on a subtree before editing. The
tree nodes carry parser-owned export candidates and `__all__` contract kind, so
the agent sees public API names without re-reading source text. The
harness turns those facts into `PY-MOD-R007` and `PY-AGENT-POLICY-007` findings; it
does not re-parse Python source to infer tree shape or dependency direction.
Project policy uses the same parser metadata to keep declared import names
and entry point targets aligned with parser-visible project owners.

The same parser facts back `render_python_reasoning_tree()`, a compact
agent-facing tree snapshot. That render is intentionally separate from JSON:
agents can inspect package branches, public leaves, child names, and owner
shadows, plus compact exports, internal imports, and declared project metadata,
before choosing a repair surface.

## Runner Modes

Use `run_python_project_harness()` or `assert_python_project_harness_clean()`
when a caller has a project root. The project runner scans all Python files
under the project root by default, with cache/build/environment directories
excluded. `src/` and `tests/` remain source/test classification roots for
project policy; they do not narrow parser coverage. `PythonHarnessConfig` can
change source-root classification, test-root classification, extra external
project paths, and test inclusion behavior.

Use `run_python_lang_harness()` or `assert_python_lang_harness_clean()` for
explicit files or directories. This runner is useful for focused parser checks
and editor integrations; project-scoped rule packs only emit findings when a
project scope is available.

## Pytest Embedding

The assertion helper raises `AssertionError` with the compact rendered report
when configured-blocking findings exist:

```python
from pathlib import Path

from python_lang_project_harness import assert_python_project_harness_clean


def test_python_project_harness_policy() -> None:
    assert_python_project_harness_clean(Path("."))
```

`python_project_harness_test()` returns a pytest-collectable callable for
projects that prefer a one-line mount. Downstream projects can import it from
`python_lang_project_harness.pytest` and assign it to a test name.

The package also exposes a pytest plugin through the `pytest11` entry point.
When installed as a test/dev dependency, pytest loads the plugin and accepts
`--python-project-harness`. The plugin only inserts the harness item when that
option is enabled, so installing the package does not silently add a policy
gate.

## CLI Embedding

`asp-python check [--json] [PROJECT_ROOT]` runs the same default project
runner. Compact text is the default output. `--json` emits the structured
`PythonHarnessReport` payload. `asp-python search ...` renders bounded
semantic-search packets from parser-owned facts. The CLI is a thin adapter over
library APIs: it does not own workflow orchestration or project-specific
policy.

## Blocking And Advice

`Warning` and `Error` findings are blocking by default. `Info` findings are
advisory. `PY-AGENT-*` rules are intentionally `Info` so agents receive repair
hints without making every legibility concern a hard gate.

:RELATIONS:
:LINKS: [Rule Catalog](../03_features/201_rule_catalog.md), [Runner Modes](../03_features/202_runner_modes.md), [CLI](../03_features/203_cli.md)
:END:
