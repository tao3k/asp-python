"""Validate development command log sequencing and hook context inheritance."""

from __future__ import annotations

import json
from pathlib import Path

from asp_python._dev_command_log import start_dev_command_log


def test_dev_command_log_records_ordered_active_context_events(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "project"
    trace = tmp_path / "trace"
    project.mkdir()
    trace.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "dev-log-fixture"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    project_root_hash = _stable_hash_hex(str(project))
    context_dir = trace / "dev-context"
    context_dir.mkdir()
    (context_dir / f"{project_root_hash}.json").write_text(
        json.dumps(
            {
                "hookRunId": "hook-run-py",
                "parentEventId": "hook-parent-py",
                "sessionId": "session-py",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SEMANTIC_PROTOCOL_DEV_MODE", "1")
    monkeypatch.setenv("SEMANTIC_PROTOCOL_TRACE_DIR", str(trace))
    monkeypatch.delenv("SEMANTIC_PROTOCOL_PARENT_EVENT_ID", raising=False)
    monkeypatch.delenv("SEMANTIC_PROTOCOL_SESSION_ID", raising=False)
    monkeypatch.delenv("SEMANTIC_PROTOCOL_HOOK_RUN_ID", raising=False)
    monkeypatch.delenv("CODEX_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("TERM_SESSION_ID", raising=False)
    monkeypatch.delenv("CODEX_HOOK_RUN_ID", raising=False)
    monkeypatch.delenv("AGENT_HOOK_RUN_ID", raising=False)

    log = start_dev_command_log(
        ["search", "lexical", "metadata", str(project)], project
    )
    log.finish(0)

    command_dir = trace / "python" / "asp-python" / "commands"
    entries = list(command_dir.glob("*.jsonl"))
    assert len(entries) == 1
    assert entries[0].name.startswith("20")
    assert "T" in entries[0].name
    assert "-000001-" in entries[0].name

    event = json.loads(entries[0].read_text(encoding="utf-8"))
    assert event["schemaId"] == "agent.semantic-protocols.dev-command-log"
    assert event["languageId"] == "python"
    assert event["providerId"] == "asp-python"
    assert event["sessionId"] == "session-py"
    assert event["sessionOrdinal"] == 1
    assert event["parentEventId"] == "hook-parent-py"
    assert event["hookRunId"] == "hook-run-py"
    assert event["fields"]["contextSource"] == "active-context"
    assert "stdout" not in event
    assert "stderr" not in event


def _stable_hash_hex(value: str) -> str:
    hash_value = 0xCBF29CE484222325
    for byte in value.encode("utf-8"):
        hash_value ^= byte
        hash_value = (hash_value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{hash_value:016x}"
