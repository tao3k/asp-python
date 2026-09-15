"""Resolve project, session, and trace paths for dev command logs."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT_ANCHORS = (
    "Cargo.toml",
    "package.json",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "Project.toml",
    ".git",
)


@dataclass(frozen=True, slots=True)
class SessionContext:
    session_id: str
    source: str
    hook_run_id: str | None = None
    parent_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class _LockFile:
    path: Path

    def __enter__(self) -> None:
        for _ in range(50):
            try:
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                os.write(fd, str(os.getpid()).encode("utf-8"))
                os.close(fd)
                return
            except FileExistsError:
                time.sleep(0.005)
        raise TimeoutError(
            f"failed to acquire dev command log counter lock: {self.path}"
        )

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def infer_project_root(args: list[str] | tuple[str, ...], cwd: Path) -> Path | None:
    for arg in reversed(args):
        if arg.startswith("-"):
            continue
        candidate = Path(arg)
        if not candidate.is_absolute():
            candidate = cwd / candidate
        root = project_root_from_path(candidate)
        if root is not None:
            return root
    return project_root_from_path(cwd)


def project_root_from_path(candidate: Path) -> Path | None:
    cursor = candidate if candidate.is_dir() else candidate.parent
    while True:
        if any((cursor / anchor).exists() for anchor in PROJECT_ANCHORS):
            return cursor
        if cursor.parent == cursor:
            return None
        cursor = cursor.parent


def resolve_log_root(project_root: Path, project_root_hash: str) -> Path | None:
    trace_dir = env_non_empty("SEMANTIC_PROTOCOL_TRACE_DIR")
    if trace_dir is not None:
        return path_from_env(trace_dir, project_root)
    prj_cache_home = env_non_empty("PRJ_CACHE_HOME")
    if prj_cache_home is not None:
        return path_from_env(prj_cache_home, project_root) / "semantic_protocol"
    xdg_cache_home = env_non_empty("XDG_CACHE_HOME")
    if xdg_cache_home is not None:
        return (
            Path(xdg_cache_home)
            / "agent-semantic-protocols"
            / project_root_hash
            / "semantic_protocol"
        )
    home = env_non_empty("HOME")
    if home is not None:
        return (
            Path(home)
            / ".cache"
            / "agent-semantic-protocols"
            / project_root_hash
            / "semantic_protocol"
        )
    return None


def resolve_session_context(log_root: Path, project_root_hash: str) -> SessionContext:
    env_session_id = env_first(
        (
            "SEMANTIC_PROTOCOL_SESSION_ID",
            "CODEX_SESSION_ID",
            "CLAUDE_SESSION_ID",
            "TERM_SESSION_ID",
        )
    )
    env_hook_run_id = env_first(
        (
            "SEMANTIC_PROTOCOL_HOOK_RUN_ID",
            "CODEX_HOOK_RUN_ID",
            "AGENT_HOOK_RUN_ID",
        )
    )
    env_parent_event_id = env_first(("SEMANTIC_PROTOCOL_PARENT_EVENT_ID",))
    if (
        env_session_id is not None
        or env_hook_run_id is not None
        or env_parent_event_id is not None
    ):
        session_id = env_session_id or (
            f"hook-{stable_hash_hex(env_hook_run_id)}"
            if env_hook_run_id is not None
            else f"project-{project_root_hash}"
        )
        return SessionContext(
            hook_run_id=env_hook_run_id,
            parent_event_id=env_parent_event_id or env_hook_run_id,
            session_id=session_id,
            source="env",
        )

    marker = read_active_context(log_root, project_root_hash)
    if marker is not None:
        return marker
    return SessionContext(
        session_id=f"project-{project_root_hash}", source="project-fallback"
    )


def read_active_context(
    log_root: Path, project_root_hash: str
) -> SessionContext | None:
    marker = log_root / "dev-context" / f"{project_root_hash}.json"
    try:
        stat = marker.stat()
        if time.time() - stat.st_mtime > 30 * 60:
            return None
        data = json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return SessionContext(
        hook_run_id=string_field(data.get("hookRunId")),
        parent_event_id=string_field(data.get("parentEventId")),
        session_id=string_field(data.get("sessionId"))
        or f"project-{project_root_hash}",
        source="active-context",
    )


def allocate_session_ordinal(log_root: Path, session_id: str) -> int:
    directory = log_root / "python" / "asp-python" / "sessions"
    counter_path = directory / f"{sanitize_file_component(session_id)}.counter"
    lock_path = directory / f"{sanitize_file_component(session_id)}.lock"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with _LockFile(lock_path):
            try:
                current = int(counter_path.read_text(encoding="utf-8").strip())
            except Exception:
                current = 0
            next_value = current + 1
            counter_path.write_text(str(next_value), encoding="utf-8")
            return next_value
    except Exception:
        return 0


def path_from_env(value: str, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def env_truthy(name: str) -> bool:
    return os.environ.get(name) in {"1", "true", "TRUE", "yes", "YES", "on", "ON"}


def env_first(names: tuple[str, ...]) -> str | None:
    for name in names:
        value = env_non_empty(name)
        if value is not None:
            return value
    return None


def env_non_empty(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def string_field(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def sanitize_file_component(value: str) -> str:
    sanitized = "".join(
        char if char.isascii() and (char.isalnum() or char in {"_", "-", "."}) else "_"
        for char in value
    )
    return sanitized or "unknown"


def stable_hash_hex(value: str | None) -> str:
    hash_value = 0xCBF29CE484222325
    for byte in (value or "").encode("utf-8"):
        hash_value ^= byte
        hash_value = (hash_value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{hash_value:016x}"
