"""Write development-only asp-python command log events."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ._dev_command_log_command import (
    NormalizedCommand,
    command_payload,
    normalize_command,
    redact_argv,
)
from ._dev_command_log_context import (
    allocate_session_ordinal,
    env_truthy,
    infer_project_root,
    resolve_log_root,
    resolve_session_context,
    sanitize_file_component,
    stable_hash_hex,
)

SCHEMA_ID = "agent.semantic-protocols.dev-command-log"
SCHEMA_VERSION = "1"
PROTOCOL_ID = "agent.semantic-protocols.semantic-language"
PROTOCOL_VERSION = "1"


class DevCommandLog:
    def __init__(
        self,
        *,
        argv: list[str],
        command: NormalizedCommand,
        context_source: str,
        cwd: Path,
        event_id: str,
        hook_run_id: str | None,
        log_file: Path,
        parent_event_id: str | None,
        project_root: Path,
        project_root_hash: str,
        session_id: str,
        session_ordinal: int,
        started_at_monotonic: float,
        started_at_utc: str,
    ) -> None:
        self.argv = argv
        self.command = command
        self.context_source = context_source
        self.cwd = cwd
        self.event_id = event_id
        self.hook_run_id = hook_run_id
        self.log_file = log_file
        self.parent_event_id = parent_event_id
        self.project_root = project_root
        self.project_root_hash = project_root_hash
        self.session_id = session_id
        self.session_ordinal = session_ordinal
        self.started_at_monotonic = started_at_monotonic
        self.started_at_utc = started_at_utc

    def finish(self, exit_code: int) -> None:
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            event = self._event_payload(exit_code)
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, separators=(",", ":")))
                handle.write("\n")
        except Exception:
            return

    def _event_payload(self, exit_code: int) -> dict[str, Any]:
        finished_at = utc_timestamp()
        event: dict[str, Any] = {
            "schemaId": SCHEMA_ID,
            "schemaVersion": SCHEMA_VERSION,
            "protocolId": PROTOCOL_ID,
            "protocolVersion": PROTOCOL_VERSION,
            "timestampUtc": finished_at,
            "startedAtUtc": self.started_at_utc,
            "finishedAtUtc": finished_at,
            "eventId": self.event_id,
            "sessionId": self.session_id,
            "sessionOrdinal": self.session_ordinal,
            "languageId": "python",
            "providerId": "asp-python",
            "binary": "asp-python",
            "argv": self.argv,
            "cwd": str(self.cwd),
            "projectRoot": str(self.project_root),
            "projectRootHash": self.project_root_hash,
            "command": command_payload(self.command),
            "result": {
                "exitCode": exit_code,
                "elapsedMs": max(
                    0,
                    int((time.monotonic() - self.started_at_monotonic) * 1000),
                ),
                "stdoutBytes": 0,
                "stderrBytes": 0,
                "status": "success" if exit_code == 0 else "failure",
            },
            "fields": {
                "contextSource": self.context_source,
                "logFileNaming": "utc-second-session-ordinal-event",
                "outputBytesMeasured": False,
                "sequenceScope": "session",
            },
        }
        if self.parent_event_id is not None:
            event["parentEventId"] = self.parent_event_id
        if self.hook_run_id is not None:
            event["hookRunId"] = self.hook_run_id
        return event


class DisabledDevCommandLog:
    def finish(self, exit_code: int) -> None:
        return


def start_dev_command_log(
    args: list[str] | tuple[str, ...],
    cwd: Path | None = None,
) -> DevCommandLog | DisabledDevCommandLog:
    if not env_truthy("SEMANTIC_PROTOCOL_DEV_MODE"):
        return DisabledDevCommandLog()

    selected_cwd = Path.cwd() if cwd is None else cwd
    project_root = infer_project_root(args, selected_cwd) or selected_cwd
    project_root_hash = stable_hash_hex(str(project_root))
    log_root = resolve_log_root(project_root, project_root_hash)
    if log_root is None:
        return DisabledDevCommandLog()

    session = resolve_session_context(log_root, project_root_hash)
    session_ordinal = allocate_session_ordinal(log_root, session.session_id)
    started_at_ms = int(time.time() * 1000)
    event_id = f"asp-python-{started_at_ms}-{os.getpid()}-{session_ordinal:06d}"
    log_file = (
        log_root
        / "python"
        / "asp-python"
        / "commands"
        / f"{utc_file_timestamp()}-{session_ordinal:06d}-{sanitize_file_component(event_id)}.jsonl"
    )
    argv = ["asp-python", *redact_argv(list(args))]
    return DevCommandLog(
        argv=argv,
        command=normalize_command(argv),
        context_source=session.source,
        cwd=selected_cwd,
        event_id=event_id,
        hook_run_id=session.hook_run_id,
        log_file=log_file,
        parent_event_id=session.parent_event_id,
        project_root=project_root,
        project_root_hash=project_root_hash,
        session_id=session.session_id,
        session_ordinal=session_ordinal,
        started_at_monotonic=time.monotonic(),
        started_at_utc=utc_timestamp(),
    )


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_file_timestamp() -> str:
    return utc_timestamp().replace(":", "-")
