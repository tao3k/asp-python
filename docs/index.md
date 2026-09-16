# ASP Python: Map Of Content

:PROPERTIES:
:ID: efd68dc9011b23c38164eb503920b77bdfdd6c68
:TYPE: INDEX
:STATUS: ACTIVE
:LAST_SYNC: 2026-04-30
:END:

Documentation surface for ASP Python. The
README stays compact; durable package details live here so runner modes, rule
catalogs, and embedding contracts can evolve without turning the package
entrypoint into a catch-all reference page.

## 01_core: Architecture And Foundation

- [ASP Python Boundary](01_core/101_asp_python_boundary.md): package ownership,
  parser boundary, project runner, explicit-path runner, pytest embedding, and
  non-goals.

## 03_features: Functional Ledger

- [Rule Catalog](03_features/201_rule_catalog.md): default rule packs,
  blocking/advisory split, catalog functions, compact rendering policy, and
  snapshot coverage.
- [Runner Modes](03_features/202_runner_modes.md): project runner,
  explicit-path runner, shared config, and path validation.
- [CLI](03_features/203_cli.md): console script, module entrypoint, output
  modes, and exit-code contract.
- [Pytest Dev Dependency](03_features/204_pytest.md): pytest plugin entry
  point, one-line test helper, and downstream dev dependency examples.
- [Verification Planning](03_features/205_verification.md): parser-backed
  verification tasks, profile hints, receipts, waivers, and report artifacts.

:RELATIONS:
:LINKS: [ASP Python Boundary](01_core/101_asp_python_boundary.md), [Rule Catalog](03_features/201_rule_catalog.md), [Runner Modes](03_features/202_runner_modes.md), [CLI](03_features/203_cli.md), [Pytest Dev Dependency](03_features/204_pytest.md), [Verification Planning](03_features/205_verification.md)
:END:

---

:FOOTER:
:STANDARDS: v2.0
:LAST_SYNC: 2026-04-30
:END:
