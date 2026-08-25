"""Handle semantic AST patch preview commands for Python agent repair flows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TextIO

from ._cli_args import ProtocolArgs

RECEIPT_SCHEMA_ID = "agent.semantic-protocols.semantic-ast-patch-receipt"
AST_PATCH_PROTOCOL_ID = "agent.semantic-protocols.ast-patch"

SCHEMA_OPERATIONS = {
    "append_to_block",
    "insert_before_statement",
    "insert_after_statement",
    "replace_statement",
    "replace_expression",
    "replace_call_arg",
    "insert_import",
    "remove_import",
    "remove_statement",
    "remove_item",
    "replace_item",
}


def run_ast_patch_command(
    args: ProtocolArgs,
    *,
    project_root: Path,
    stdout: TextIO,
    stdin: str,
) -> int:
    if args.packet_path == "-":
        packet_text = stdin
    elif args.packet_path is not None:
        packet_text = (project_root / args.packet_path).read_text(encoding="utf-8")
    else:
        packet_text = ""
    stdout.write(render_unsupported_operation_receipt(packet_text, project_root))
    stdout.write("\n")
    return 0


def render_unsupported_operation_receipt(packet_text: str, project_root: Path) -> str:
    try:
        packet = json.loads(packet_text)
    except json.JSONDecodeError as error:
        return json.dumps(
            _receipt(
                language_id="python",
                target={"ownerPath": None, "locator": None, "read": None},
                operation=None,
                failure_kind="invalid-packet",
                failures=[f"invalid JSON packet: {error}"],
                verification=[],
                project_root=project_root,
            ),
            sort_keys=True,
        )

    target = packet.get("target") if isinstance(packet, dict) else None
    operation = packet.get("operation") if isinstance(packet, dict) else None
    op = operation.get("op") if isinstance(operation, dict) else None
    schema_operation = op if isinstance(op, str) and op in SCHEMA_OPERATIONS else None
    failure_kind = "unsupported-operation" if op is not None else "invalid-packet"
    failure = (
        f"python provider ast-patch dry-run does not support operation: {op}"
        if op is not None
        else "packet operation.op is required"
    )

    return json.dumps(
        _receipt(
            language_id="python",
            target={
                "ownerPath": _target_string(target, "ownerPath"),
                "locator": _target_string(target, "locator"),
                "read": _target_string(target, "read"),
            },
            operation=schema_operation,
            failure_kind=failure_kind,
            failures=[failure],
            verification=["packet-parsed"],
            project_root=project_root,
        ),
        sort_keys=True,
    )


def _receipt(
    *,
    language_id: str,
    target: dict[str, str | None],
    operation: str | None,
    failure_kind: str,
    failures: list[str],
    verification: list[str],
    project_root: Path,
) -> dict[str, object]:
    return {
        "schemaId": RECEIPT_SCHEMA_ID,
        "schemaVersion": "1",
        "protocolId": AST_PATCH_PROTOCOL_ID,
        "protocolVersion": "1",
        "status": "failed",
        "mode": "dry-run",
        "capability": "provider-ast-dry-run",
        "mutationAvailable": False,
        "languageId": language_id,
        "target": target,
        "operation": operation,
        "supportedOperations": [],
        "mechanicalEditPlan": None,
        "verification": verification,
        "failureKind": failure_kind,
        "failures": failures,
        "next": (
            "asp python query --selector <exact-structural-selector> "
            f"--projection source --workspace {project_root}"
        ),
    }


def _target_string(target: object, key: str) -> str | None:
    if not isinstance(target, dict):
        return None
    value = target.get(key)
    return value if isinstance(value, str) else None
