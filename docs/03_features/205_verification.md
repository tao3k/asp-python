# Verification Planning

:PROPERTIES:
:ID: 884403d80a274f9d975119079f286b5e
:TYPE: FEATURE
:STATUS: ACTIVE
:LAST_SYNC: 2026-05-03
:END:

Python verification planning is a library-first Agent contract. The harness
does not run benchmark, security, stress, or chaos tools. It uses parser-owned
project facts to produce external obligations that an Agent skill can satisfy
with receipts or complete waivers.

```python
from asp_python import (
    PythonOwnerResponsibility,
    PythonVerificationProfileHint,
    PythonVerificationTaskKind,
    default_python_harness_config,
    plan_python_project_verification_with_config,
    render_python_verification_plan,
)

config = default_python_harness_config().with_verification_profile_hint(
    PythonVerificationProfileHint(
        "src/pkg/api.py",
        (PythonOwnerResponsibility.PUBLIC_API,),
    )
    .with_task_kinds((PythonVerificationTaskKind.SECURITY,))
    .with_rationale("this public API needs a security review")
)

plan = plan_python_project_verification_with_config(".", config)
print(render_python_verification_plan(plan))
```

The compact renderer emits active `[verify]` tasks and `[verify-report]`
obligations. Report helpers can render or persist `verification_plan.json`,
`verification_task_index.json`, and `performance_index.json`. Source manifests
only list source-baseline artifacts; runtime manifests carry the complete
bundle with `project_root`, so an Agent can reconstruct the verification
contract from the cache without reading source-control-only baselines first.

## Parser Priority

Profile hints and dependency signals are configuration, not authority. Parser
facts decide whether an owner path exists and whether a declared responsibility
matches the source tree. When configuration drifts from parser facts, the plan
emits a `responsibility_review` task instead of trusting the stale hint.

`build_python_verification_profile_index(...)` is the low-noise discovery
surface for this policy. Each index exposes parser-suggested candidates and
`active_profile_hints()` for config-ready hints that still need attention. The
same parser-visible owner map is used by the planner, so metadata owners such
as `pyproject.toml` and script entry-point owners can be accepted without
falling into false `responsibility_review` tasks.

When parser facts produce candidates before any profile hint is configured,
the compact renderer emits a single `[verify-profile] profile_hints` reminder
so the Agent knows to add `PythonVerificationProfileHint` entries instead of
treating the missing profile as an empty project.

Profile candidates are branch-first: public package branches aggregate their
child-module public API signal, while unowned public leaves still surface as
their own candidates. When the same owner has multiple responsibilities, the
index merges them into one candidate and one config-ready hint.
For drift, compact output includes both `configured` and `suggest`, so an Agent
can patch the policy from the profile index without reparsing `pyproject.toml`.

## Config Surface

The verification policy supports profile hints, dependency signals, receipts,
waivers, responsibility task-kind mappings, task contracts, skill bindings, and
skill descriptors through `PythonVerificationPolicy` or
`[tool.asp-python.verification]`.

```toml
[tool.asp-python.verification]
profile_hints = [
  { owner_path = "src/pkg/api.py", responsibilities = ["public_api"], task_kinds = ["security"], rationale = "authz-sensitive public API" },
]

[tool.asp-python.verification.task_contracts]
security = { phase = "before_release", summary = "security skill must report authz evidence", requirements = [{ label = "authz", detail = "tenant authorization result" }] }

[tool.asp-python.verification.skill_bindings]
security = { skill = "python-security-review", adapter = "bandit" }

[tool.asp-python.verification.skill_descriptors]
python-security-review = { task_kind = "security", adapter = "bandit", summary = "run bandit plus tenant authz probes", requirements = [{ label = "bandit", detail = "bandit report artifact" }] }
```

When a task has a skill binding and matching descriptor, compact verification
output stays short with `skill=<binding>` and `contract_ref=<descriptor>`.
Agents can call `render_python_verification_skill_contracts(plan)` only when
they need to expand the referenced contract.

:RELATIONS:
:LINKS: [Harness Boundary](../01_core/101_harness_boundary.md), [CLI](203_cli.md)
:END:
