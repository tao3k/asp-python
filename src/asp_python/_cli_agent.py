"""Agent-facing guide and doctor rendering for the Python harness CLI."""

from __future__ import annotations

import json
from pathlib import Path

from ._semantic_provider_doctor import semantic_provider_doctor_document


def render_agent_guide(project_root: Path) -> str:
    project = str(project_root)
    workspace = "--workspace <workspace-root>"
    root = workspace
    return (
        "\n".join(
            (
                f"[asp-python-guide] project={project}",
                (
                    "|catalog reasoningProfiles=owner-query,query-deps,owner-tests,"
                    "finding-frontier,feature-cfg entries=owner-query,query-deps,"
                    "owner-tests routes=syntax-locate,exact-source,callable-skeleton"
                ),
                "|routing evidence-state prime=owner-map-only pipe=ambiguous-query "
                "owner=known-owner selector=exact-parser-id deps=known-dependency "
                "tests=known-owner ingest=stdin",
                (
                    f"|route syntax-locate selectors=S:tree-sitter-query,Scope:owner-or-structural "
                    f"returns=locator,capture,frontier code=false cmd=asp python "
                    f"query --treesitter-query "
                    f"'(function_definition name: (identifier) @function.name)' "
                    f"--selector <owner-path-or-structural-scope> {workspace}"
                ),
                f"|route exact-source selectors=R:exact-selector returns=source cmd=asp python query --selector <exact-structural-selector> --projection source {workspace}",
                f"|route callable-skeleton selectors=R:exact-callable-selector returns=callable-skeleton cmd=asp python query --selector <exact-structural-selector> --projection callable-skeleton {workspace}",
                f"|cmd prime=asp python search prime {root} --view seeds condition=owner-map-unknown",
                f"|cmd pipe=asp python search pipe <query> {root} --view seeds condition=ambiguous-query",
                f"|cmd owner=asp python search owner <owner-path> {root} --view seeds",
                (
                    f"|cmd reasoning-owner-tests=asp python search reasoning "
                    f"owner-tests --owner <owner-path> {root} --view seeds"
                ),
                (
                    f"|cmd reasoning-owner-query=asp python search reasoning "
                    f"owner-query --owner <owner-path> --query <symbol> "
                    f"{root} --view seeds"
                ),
                (
                    f"|cmd reasoning-query-deps=asp python search reasoning "
                    f"query-deps --query <symbol> --dependency <pkg> "
                    f"{root} --view seeds"
                ),
                f"|cmd catalog-json=asp python query --catalog declarations --json {root}",
                (
                    f"|cmd syntax-locate=asp python query --treesitter-query "
                    f"'(function_definition name: (identifier) @function.name)' "
                    f"--selector <owner-path-or-structural-scope> {workspace}"
                ),
                f"|cmd exact-source=asp python query --selector <exact-structural-selector> --projection source {workspace}",
                f"|cmd callable-skeleton=asp python query --selector <exact-structural-selector> --projection callable-skeleton {workspace}",
                (
                    f"|cmd policy=asp python search policy <rule-id-or-alias> "
                    f"owner tests {root} --view seeds"
                ),
                f"|cmd lexical=asp python search lexical <query> owner tests {root} --view seeds",
                "|cmd ast-patch=asp python ast-patch dry-run --packet <semantic-ast-patch.json|->",
                f"|cmd evidence-graph=asp python evidence graph --json {root}",
                f"|cmd evidence-analyze=asp python evidence analyze --json {root}",
                f"|cmd deps=asp python search deps <pkg[@ver][::api]> {root}",
                f"|cmd env=asp python search env [term ...] {workspace} --view seeds",
                f"|cmd runtime-source=asp python search runtime-source [term ...] {workspace} --view seeds",
                f"|cmd lang=asp python search lang [term ...] {workspace} --view seeds",
                f"|cmd std=asp python search std [term ...] {workspace} --view seeds",
                f"|cmd capability=asp python search capability [term ...] {workspace} --view seeds",
                f"|cmd extension=asp python search extension <extension> [term ...] {workspace} --view seeds",
                f"|cmd pattern=asp python search pattern <feature-or-extension> [term ...] {workspace} --view seeds",
                f"|cmd compare=asp python search compare <axis> [left right] {workspace} --view seeds",
                f"|pipe <candidate-lines> | asp python search ingest {root} --view seeds",
                "|policy authority=asp-python-api trigger=pytest-plugin",
                "|rule agent hook install/runtime is owned by asp",
                (
                    "|rule selector queries do not need a trailing project root; "
                    "--workspace <workspace-root> is the independent workspace override"
                ),
                (
                    "|rule syntax query ABI is compiled by asp; provider projects "
                    "native parser facts into tree-sitter-compatible captures"
                ),
                (
                    "|rule syntax predicates supported=#eq?,#any-eq?,#any-of?,"
                    "#match?,#any-match?,#not-eq?,#not-match? "
                    "unsupported=none unsupportedReported=true"
                ),
                "|rule exact query requires a parser-owned selector and an explicit source or callable-skeleton projection",
                (
                    "|rule displayLineRange/sourceLocatorHint are display hints; "
                    "execute structural selectors or owner/symbol routes, not line ranges"
                ),
                "|rule Python discovery uses search --view seeds; query only materializes an exact structural selector",
                (
                    "|rule provider-knowledge-axes env/lang/std/pattern/runtime-source "
                    "return facts or explicit frontier gaps; do not fill missing "
                    "facts from memory"
                ),
                (
                    "|rule use the asp python facade; run one command at a time; "
                    "no raw Python source reads"
                ),
                "|subagent give one |cmd or |pipe line; require evidence/missing/next/risk",
            )
        )
        + "\n"
    )


def render_agent_doctor(project_root: Path) -> str:
    from . import _semantic_language_ids as ids
    from ._semantic_language import python_semantic_language_registration

    registration = python_semantic_language_registration()
    return (
        "\n".join(
            (
                "[agent-doctor] "
                f"status=ok protocol={ids.SEMANTIC_LANGUAGE_PROTOCOL_ID} "
                f"registry=semantic-language-registry.v{ids.SEMANTIC_LANGUAGE_REGISTRY_VERSION}",
                f"|project {project_root}",
                (
                    f"|language id={ids.PYTHON_LANGUAGE_ID} provider={ids.PYTHON_PROVIDER_ID} "
                    f"binary={ids.PYTHON_BINARY}"
                ),
                f"|namespace {ids.PYTHON_PROVIDER_NAMESPACE}",
                f"|method {','.join(registration['methods'])}",
                "|schema semantic-search-packet.v1",
            )
        )
        + "\n"
    )


def render_agent_doctor_json(project_root: Path) -> str:
    return (
        json.dumps(
            semantic_provider_doctor_document(),
            separators=(",", ":"),
        )
        + "\n"
    )
