# Development

## Format, Test, Lint

```shell
.devenv/devenv-profile-exec uv run --project languages/asp-python --group test ruff format --check languages/asp-python/src languages/asp-python/tests
.devenv/devenv-profile-exec uv run --project languages/asp-python --group test ruff check languages/asp-python/src languages/asp-python/tests
.devenv/devenv-profile-exec uv run --project languages/asp-python --group test pytest languages/asp-python/tests -q
.devenv/devenv-profile-exec uv run --project languages/asp-python --group test asp-python languages/asp-python
.devenv/devenv-profile-exec uv run --project languages/asp-python --group test asp-python --agent-snapshot languages/asp-python
.devenv/devenv-profile-exec uv build languages/asp-python
.devenv/devenv-profile-exec git diff --check
```

Use `.devenv/devenv-profile-exec` from the repository root so the captured
devenv-managed Python and `uv` environment are used consistently.

GitHub Actions runs the same validation surface without `direnv`: `uv sync
--group test --locked`, ruff format/check, pytest, ASP Python self-check, package build,
agent snapshot, and `git diff --check`.

## Library Boundary

This repo is a standalone Python library project. It ships:

- `python_lang_parser` for Python-native parser facts
- `asp_python` for discovery, rule packs, rendering,
  and pytest embedding

Keep these boundaries separate. Parser modules should not know about project
policy, pytest, or agent repair wording. ASP Python modules should consume parser
reports and emit deterministic findings.

## Self-Applied Policy

`tests/unit/test_self_hosting.py` mounts the ASP Python against this repo.
When adding tests, keep behavior coverage under `tests/unit` and avoid
scattered `tests/test_*.py` files at the test root.

Default assertions block on `Warning` and `Error`. `PY-AGENT-*` rules stay
`Info`: rendered by default as repair advice, but non-blocking unless a caller
opts into stricter severity selection.

The CLI is part of that same contract. Keep `asp-python` as a thin
adapter over the library runner and renderers.

## Renderer Contract

Compact text is the primary agent-facing repair surface. It should remain small:
rule id, location, optional source line, pointer label, and one `Required:`
contract line. Use `render_asp_python_report_json()` for tooling that needs
the full structured payload.

## Snapshot Workflow

Rendered output and policy diagnostics are locked under `tests/unit/snapshots`.
Normal tests compare snapshots only. Refresh them intentionally:

```shell
.devenv/devenv-profile-exec env ASP_PYTHON_UPDATE_SNAPSHOTS=1 \
  uv run --project languages/asp-python --group test pytest \
  languages/asp-python/tests/unit/asp_python/test_render_snapshots.py \
  languages/asp-python/tests/unit/asp_python/test_agent_policy_snapshots.py \
  languages/asp-python/tests/unit/asp_python/test_policy_snapshots.py -q
```

Review the resulting `.snap` diff before keeping it. Snapshot changes are
policy changes: they alter what agents and humans see in compact diagnostics.
