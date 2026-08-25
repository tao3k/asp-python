# Pytest Dev Dependency

:PROPERTIES:
:ID: 50de91fe959b4d9e8833d1746430bf79
:TYPE: FEATURE
:STATUS: ACTIVE
:LAST_SYNC: 2026-04-30
:END:

`python-lang-project-harness` is designed to be loaded by downstream Python
projects as a test/dev dependency. The pytest surface has two supported entry
points: an auto-loaded pytest plugin and an explicit test helper.

## Dev Dependency Plugin

Add the package to the downstream test dependency group together with pytest:

```toml
[dependency-groups]
test = [
  "pytest>=8",
  "python-lang-project-harness[pytest]>=0.1.0",
]

[tool.pytest.ini_options]
addopts = ["--python-project-harness"]
```

The distribution exposes this plugin entry point:

```toml
[project.entry-points.pytest11]
python_lang_project_harness = "python_lang_project_harness.pytest_plugin"
```

Pytest auto-loads the plugin when the package is installed, but the harness is
quiet unless `--python-project-harness` is enabled. This keeps the package safe
as a normal library dependency while making the policy gate easy to opt into
from pytest config.

Project policy validates this wiring. If parser-owned `pyproject.toml` facts
show that a project depends on `python-lang-project-harness` for test/dev use,
the project must expose either `--python-project-harness` in pytest addopts or
an explicit `python_project_harness_test()` callable. This keeps the dependency
from becoming decorative metadata that CI can bypass.

Project-local policy can live beside pytest config in `pyproject.toml`:

```toml
[tool.python-lang-project-harness]
disabled_rule_ids = ["PY-MOD-R002"]
blocking_rule_ids = ["PY-AGENT-POLICY-007"]
```

Supported plugin options:

- `--python-project-harness`: collect and run one harness item.
- `--python-project-harness-root PATH`: choose the project root; defaults to
  pytest `rootdir`.
- `--python-project-harness-no-tests`: skip parsing test files while still
  evaluating tests-root layout.
- `--python-project-harness-source-dir NAME`: add one source classification
  root name; can be repeated.
- `--python-project-harness-test-dir NAME`: add one test classification root
  name; can be repeated.
- `--python-project-harness-extra-path NAME`: add one external project path;
  can be repeated.
- `--python-project-harness-disable-rule RULE_ID`: suppress one stable rule
  id; can be repeated.
- `--python-project-harness-block-rule RULE_ID`: promote one stable rule id to
  blocking; can be repeated.
- `--python-project-harness-error-only`: fail only on parser errors.
- `--python-project-harness-no-advice`: hide non-blocking advice in assertion
  output.

## Explicit Test Helper

Projects that prefer a committed test file can mount the same runner directly:

```python
from python_lang_project_harness.pytest import python_project_harness_test

test_python_project_harness_policy = python_project_harness_test()
```

The helper defaults to `Path(".")` and returns a pytest-collectable callable.
Callers can pass the same project-resolution options used by the library runner:

```python
from python_lang_parser import PythonDiagnosticSeverity
from python_lang_project_harness import PythonHarnessConfig
from python_lang_project_harness.pytest import python_project_harness_test

test_python_project_harness_policy = python_project_harness_test(
    config=PythonHarnessConfig(
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
:LINKS: [Harness Boundary](../01_core/101_harness_boundary.md), [Runner Modes](202_runner_modes.md), [CLI](203_cli.md)
:END:
