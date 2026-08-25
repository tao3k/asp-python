# python-lang-project-harness

`python-lang-project-harness` is a standalone Python project harness library for
modern Python packages. It ships two library boundaries in one repo:

- `python_lang_parser`: Python-native AST, compiler, tokenize, symbol-table,
  module-shape, public-surface, and symbol-role facts.
- `python_lang_project_harness`: project discovery, deterministic rule
  packs, compact rendered diagnostics, and pytest-friendly assertions.

The harness is library-first. Callers pass a project root or explicit paths,
then decide whether to assert, render compact text, or inspect the structured
report. Compact text is the default agent repair surface; JSON is available for
tooling through `render_python_lang_harness_json()`.

`python_lang_parser` is the semantic foundation. Harness policy consumes parser
reports and parser-owned `pyproject.toml` metadata instead of re-parsing Python
source or guessing package scope in the rule layer; tests-root layout stays in
the harness.

## Quick Use

```python
from pathlib import Path

from python_lang_project_harness import (
    __version__,
    PythonOwnerResponsibility,
    PythonVerificationProfileHint,
    PythonVerificationTaskKind,
    assert_python_project_harness_clean,
    default_python_harness_config,
    plan_python_project_verification_with_config,
    render_python_lang_harness,
    render_python_reasoning_tree,
    render_python_verification_plan,
    run_python_project_harness,
)


def test_python_project_harness_policy() -> None:
    assert_python_project_harness_clean(Path("."))


report = run_python_project_harness(Path("."))
print(__version__)
print(render_python_lang_harness(report))
print(render_python_reasoning_tree(report))
```

The project runner scans the whole Python project root by default, excluding
tool/cache/build directories such as `.venv`, `__pycache__`, `build`, and
`dist`. Conventional source and test roots still classify project policy, but
they do not narrow parser coverage. The explicit path runner,
`run_python_lang_harness([...])`, is useful for focused parser and syntax
checks.
Use `PythonHarnessConfig` to change source-root classification, test-root
classification, extra external project paths, test inclusion, or blocking
severities without hardcoding project-specific policy into the library.
Project runners also read `[tool.python-lang-project-harness]` from
`pyproject.toml` when no explicit `PythonHarnessConfig` is passed, including
`disabled_rule_ids` and `blocking_rule_ids` for stable rule-id policy.
Standard `[project]` metadata such as `name`, `requires-python`,
`import-names`, scripts, and pytest entry points is parsed by
`python_lang_parser` and appears in project policy and reasoning-tree facts.
When `include_tests=False`, test files are not parsed, but tests-root layout
policy still runs. Explained local exceptions can live in
`tests/python-project-harness-rules.toml`.

For agent repair loops, `render_python_reasoning_tree(report)` emits a compact
package/module owner tree from parser-owned facts. It shows package branches,
public/internal leaves, compact export names, child names, internal import
edges, declared project import names, entry points, package roots, and owner
shadows without forcing an LLM to consume the full JSON report first. In
project-scoped runs, tree paths are rendered relative to the project root to
avoid repeating long absolute prefixes.

`render_python_project_harness_agent_snapshot(".")` and the
`--agent-snapshot` CLI mode bundle compact policy findings, reasoning-tree
facts, verification-profile reminders, and active verification tasks into one
low-noise Agent repair surface. The snapshot uses capped module summaries,
branches, public owners, import edges, and branch-first profile candidates; it
does not print clean-run file counts or empty section summaries.

The semantic-language console script exposes search, registry, and check
surfaces aligned with the Rust and TypeScript harnesses:

```shell
asp-python search workspace .
asp-python search prime .
asp-python search lexical PythonHarnessReport owner tests .
asp-python search lexical --query-set PythonHarnessReport --query-set PythonSemanticSearchOptions owner tests .
asp-python search public-external-types pytest .
asp-python search callsite PythonHarnessReport .
asp-python search deps pytest .
asp-python agent doctor --json .
asp-python agent guide .
asp-python check --full .
asp-python .
asp-python --json .
asp-python --agent-snapshot .
asp-python --source-dir lib --extra-path tools --no-tests .
python -m python_lang_project_harness .
```

## Verification Planning

Verification is a library-first Agent contract. The harness does not execute
benchmark, security, stress, or chaos tools. It plans parser-backed obligations
that external skills can satisfy with receipts or complete waivers:

```python
config = default_python_harness_config().with_verification_profile_hint(
    PythonVerificationProfileHint(
        "src/pkg/api.py",
        (PythonOwnerResponsibility.PUBLIC_API,),
    )
    .with_task_kinds((PythonVerificationTaskKind.SECURITY,))
    .with_rationale("this public API needs a security review")
)
plan = plan_python_project_verification_with_config(Path("."), config)
print(render_python_verification_plan(plan))
```

Profile hints, dependency signals, receipts, waivers, task-kind mappings, and
skill bindings are configurable through `PythonVerificationPolicy` or
`[tool.python-lang-project-harness.verification]`. Parser facts win over config
hints; mismatches become `responsibility_review` tasks instead of silent trust.
`build_python_verification_profile_index(...)` exposes `active_profile_hints()`
so Agents can turn parser-suggested owners into config-ready verification
hints. Public package branches aggregate child-module public API signals, so
large packages surface owner decisions instead of one reminder per file. Report
helpers can render or persist `verification_plan.json`,
`verification_task_index.json`, and `performance_index.json` obligations; source
manifests list only source-baseline artifacts, while runtime manifests carry
the complete bundle with `project_root`.
Profile drift output includes both configured and parser-suggested
responsibilities.

## Pytest Dev Dependency

Downstream projects can load the harness through their test/dev dependency
group:

```toml
[dependency-groups]
test = [
  "pytest>=8",
  "python-lang-project-harness[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--python-project-harness"]
```

The pytest plugin is exposed through the package `pytest11` entry point. It is
loaded by pytest when the dev dependency is installed, but it only runs the
harness when `--python-project-harness` is enabled. Projects that prefer an
explicit test file can use the public helper:

```python
from python_lang_project_harness.pytest import python_project_harness_test

test_python_project_harness_policy = python_project_harness_test()
```

## Rule Packs

Default project execution runs these packs in order:

1. `python.syntax`
2. `python.project_policy`
3. `python.modern_design`
4. `python.modularity`
5. `python.test_layout`
6. `python.agent_policy`

`Warning` and `Error` findings block assertions by default. `Info` findings,
including `PY-AGENT-*` advice, stay visible in compact diagnostics without
blocking unless a caller opts into stricter severities.

The modularity pack uses parser-owned mixed signals. `PY-MOD-R006` does not
fail a file for line count alone; it requires the effective-line budget plus a
long function span or multiple split indicators such as wide public surface,
many top-level items, or mixed responsibility groups.

Agent advice also uses package-tree facts. Broad non-facade branch packages get
owner-map advice when child count combines with public-child or effective-line
signals, which helps agents see folder-level responsibility drift during
coding without changing default blocking behavior.

Detailed package material lives under [`docs/`](docs/index.md).

## CI

GitHub Actions runs the package contract on every pull request and on pushes to
the default branch: `uv sync --group test --locked`, ruff format/check, pytest,
self-harness, agent snapshot, wheel/sdist build, and diff hygiene.
