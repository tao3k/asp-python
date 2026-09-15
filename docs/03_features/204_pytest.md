# Pytest Dev Dependency

:PROPERTIES:
:ID: 50de91fe959b4d9e8833d1746430bf79
:TYPE: FEATURE
:STATUS: ACTIVE
:LAST_SYNC: 2026-04-30
:END:

`asp-python` is designed to be loaded by downstream Python
projects as a test/dev dependency. The pytest surface has two supported entry
points: an auto-loaded pytest plugin and an explicit test helper.

## Dev Dependency Plugin

Add the package to the downstream test dependency group together with pytest:

```toml
[dependency-groups]
test = [
  "pytest>=8",
  "asp-python[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--asp-python"]
```

The distribution exposes this plugin entry point:

```toml
[project.entry-points.pytest11]
asp_python = "asp_python.pytest_plugin"
```

Pytest auto-loads the plugin when the package is installed, but ASP Python is
quiet unless `--asp-python` is enabled. This keeps the package safe
as a normal library dependency while making the policy gate easy to opt into
from pytest config.

Project policy validates this wiring. If parser-owned `pyproject.toml` facts
show that a project depends on `asp-python` for test/dev use,
the project must expose either `--asp-python` in pytest addopts or
an explicit `asp_python_test()` callable. This keeps the dependency
from becoming decorative metadata that CI can bypass.

Project-local policy can live beside pytest config in `pyproject.toml`:

```toml
[tool.asp-python]
disabled_rule_ids = ["PY-MOD-R002"]
blocking_rule_ids = ["PY-AGENT-POLICY-007"]
```

Supported plugin options:

- `--asp-python`: collect and run one ASP Python item.
- `--asp-python-root PATH`: choose the project root. When omitted,
  a single path-scoped pytest invocation uses the nearest real Python project
  metadata; mixed or workspace-level invocations default to pytest `rootdir`.
- `--asp-python-no-tests`: skip parsing test files while still
  evaluating tests-root layout.
- `--asp-python-source-dir NAME`: add one source classification
  root name; can be repeated.
- `--asp-python-test-dir NAME`: add one test classification root
  name; can be repeated.
- `--asp-python-extra-path NAME`: add one external project path;
  can be repeated.
- `--asp-python-disable-rule RULE_ID`: suppress one stable rule
  id; can be repeated.
- `--asp-python-block-rule RULE_ID`: promote one stable rule id to
  blocking; can be repeated.
- `--asp-python-error-only`: fail only on parser errors.
- `--asp-python-no-advice`: hide non-blocking advice in assertion
  output.

## Explicit Test Helper

Projects that prefer a committed test file can mount the same runner directly:

```python
from asp_python.pytest import asp_python_test

test_asp_python_policy = asp_python_test()
```

The helper defaults to `Path(".")` and returns a pytest-collectable callable.
Callers can pass the same project-resolution options used by the library runner:

```python
from python_lang_parser import PythonDiagnosticSeverity
from asp_python import AspPythonConfig
from asp_python.pytest import asp_python_test

test_asp_python_policy = asp_python_test(
    config=AspPythonConfig(
        disabled_rule_ids=frozenset({"PY-MOD-R002"}),
        blocking_rule_ids=frozenset({"PY-AGENT-POLICY-007"}),
    ),
    source_dir_names=("lib",),
    include_tests=False,
    severities=frozenset({PythonDiagnosticSeverity.ERROR}),
)
```

Both pytest entry points call the parser-backed project runner. The runner
scans the whole project root by default; source/test options classify policy
roots rather than narrowing parser coverage. The pytest layer does not own
Python parsing, source scanning semantics, or policy-specific AST logic.

:RELATIONS:
:LINKS: [ASP Python Boundary](../01_core/101_asp_python_boundary.md), [Runner Modes](202_runner_modes.md), [CLI](203_cli.md)
:END:
