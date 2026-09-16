"""Agent-facing guide and doctor rendering for the ASP Python CLI."""

from __future__ import annotations

import json
from pathlib import Path

from ._semantic_provider_doctor import semantic_provider_doctor_document


def render_agent_guide(project_root: Path) -> str:
    project = str(project_root)
    workspace = "--workspace <workspace-root>"
    return (
        "\n".join(
            (
                f"[asp-python-guide] project={project}",
                "|catalog provider=native-facts routes=syntax-locate,exact-source,callable-skeleton",
                (
                    "|route syntax-locate selectors=S:tree-sitter-query,Scope:owner-or-structural "
                    "returns=locator,capture,frontier cmd=asp search playbook "
                    "--language python --rg -n -e '<symbol>' . "
                    "--tantivy 'title:<symbol>^2 OR body:<symbol>' --syntax python "
                    "'(function_definition name: (identifier) @function.name)'"
                ),
                f"|route exact-source selectors=R:exact-selector returns=source cmd=asp query playbook --language python --selector <exact-structural-selector> --projection source {workspace}",
                f"|route callable-skeleton selectors=R:exact-callable-selector returns=callable-skeleton cmd=asp query playbook --language python --selector <exact-structural-selector> --projection callable-skeleton {workspace}",
                "|cmd playbook=asp search playbook --language python --rg -n -e <query> . --tantivy 'title:<query>^2 OR body:<query>'",
                (
                    "|cmd syntax-locate=asp search playbook --language python "
                    "--rg -n -e '<symbol>' . --tantivy 'title:<symbol>^2 OR body:<symbol>' "
                    "--syntax python '(function_definition name: (identifier) @function.name)'"
                ),
                f"|cmd exact-source=asp query playbook --language python --selector <exact-structural-selector> --projection source {workspace}",
                f"|cmd callable-skeleton=asp query playbook --language python --selector <exact-structural-selector> --projection callable-skeleton {workspace}",
                "|cmd ast-patch=asp python ast-patch dry-run --packet <semantic-ast-patch.json|->",
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
                "|rule the root ASP Client owns the only public search surface; provider-local search views are removed",
                "|rule native syntax facts remain provider-owned inputs to the root search playbook",
                (
                    "|rule use the asp python facade; run one command at a time; "
                    "no raw Python source reads"
                ),
                "|subagent give one |cmd line; require evidence/missing/next/risk",
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
                "|schema semantic-query-packet.v1",
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
