# Development

## Format, Test, Lint

```shell
direnv exec . uv run --group test ruff format --check src tests
direnv exec . uv run --group test ruff check src tests
direnv exec . uv run --group test pytest tests -q
direnv exec . uv run --group test python-project-harness .
direnv exec . uv run --group test python-project-harness --agent-snapshot .
direnv exec . uv build
direnv exec . git diff --check
```

Use `direnv exec .` so the devenv-managed Python and `uv` environment are used
consistently.

GitHub Actions runs the same validation surface without `direnv`: `uv sync
--group test --locked`, ruff format/check, pytest, self-harness, package build,
agent snapshot, and `git diff --check`.

## Library Boundary

This repo is a standalone Python library project. It ships:

- `python_lang_parser` for Python-native parser facts
- `asp_python` for discovery, rule packs, rendering,
  and pytest embedding

Keep these boundaries separate. Parser modules should not know about project
policy, pytest, or agent repair wording. Harness modules should consume parser
reports and emit deterministic findings.

## Self-Applied Policy

`tests/unit/test_self_hosting.py` mounts the project harness against this repo.
When adding tests, keep behavior coverage under `tests/unit` and avoid
scattered `tests/test_*.py` files at the test root.

Default assertions block on `Warning` and `Error`. `PY-AGENT-*` rules stay
`Info`: rendered by default as repair advice, but non-blocking unless a caller
opts into stricter severity selection.

The CLI is part of that same contract. Keep `python-project-harness` as a thin
adapter over the library runner and renderers.

## Renderer Contract

Compact text is the primary agent-facing repair surface. It should remain small:
rule id, location, optional source line, pointer label, and one `Required:`
contract line. Use `render_python_lang_harness_json()` for tooling that needs
the full structured payload.

## Snapshot Workflow

Rendered output and policy diagnostics are locked under `tests/unit/snapshots`.
Normal tests compare snapshots only. Refresh them intentionally:

```shell
ASP_PYTHON_UPDATE_SNAPSHOTS=1 direnv exec . uv run --group test pytest \
  tests/unit/harness/test_render_snapshots.py \
  tests/unit/harness/test_agent_policy_snapshots.py \
  tests/unit/harness/test_policy_snapshots.py -q
```

Review the resulting `.snap` diff before keeping it. Snapshot changes are
policy changes: they alter what agents and humans see in compact diagnostics.
