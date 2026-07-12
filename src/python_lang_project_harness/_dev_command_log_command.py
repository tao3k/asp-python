"""Normalize py-harness argv for development command logging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SECRET_FLAGS = {
    "--api-key",
    "--apikey",
    "--password",
    "--secret",
    "--token",
}

VALUE_OPTIONS = {
    "--from-hook",
    "--package",
    "--query",
    "--selector",
    "--term",
    "--view",
}

SEARCH_PIPES = {
    "dependency",
    "deps",
    "docs",
    "features",
    "lexical",
    "items",
    "owner",
    "owners",
    "prime",
    "symbol",
    "tests",
    "workspace",
}


@dataclass(frozen=True, slots=True)
class NormalizedCommand:
    namespace: str
    method: str
    pipes: tuple[str, ...]
    query: str | None
    query_set_count: int
    render_mode: str | None
    view: str | None


def redact_argv(args: list[str]) -> list[str]:
    output: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        flag = arg.split("=", 1)[0]
        if flag in SECRET_FLAGS and "=" in arg:
            output.append(f"{flag}=[REDACTED]")
        elif arg in SECRET_FLAGS:
            output.append(arg)
            if index + 1 < len(args):
                index += 1
                output.append("[REDACTED]")
        else:
            output.append(arg)
        index += 1
    return output


def normalize_command(argv: list[str]) -> NormalizedCommand:
    args = argv[1:]
    namespace_index = next(
        (index for index, arg in enumerate(args) if not arg.startswith("-")),
        -1,
    )
    namespace = (
        normalize_token(args[namespace_index]) if namespace_index >= 0 else "cli"
    )
    render_mode = option_value(args, "--view")
    query_set_count = sum(
        1 for arg in args if arg == "--query" or arg.startswith("--query=")
    )
    pipes = tuple(sorted({normalize_token(arg) for arg in args} & SEARCH_PIPES))
    view = (
        normalize_token(first_positional_after(args, namespace_index) or "")
        if namespace == "search"
        else None
    )
    if view == "unknown":
        view = None
    method = command_method(namespace, view, args, namespace_index)
    query = option_value(args, "--query") or first_query_positional(
        args,
        namespace_index,
        view,
    )
    return NormalizedCommand(
        namespace=namespace,
        method=method,
        pipes=pipes,
        query=query,
        query_set_count=query_set_count,
        render_mode=normalize_token(render_mode) if render_mode is not None else None,
        view=view,
    )


def command_payload(command: NormalizedCommand) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "namespace": command.namespace,
        "method": command.method,
        "querySetCount": command.query_set_count,
        "pipes": list(command.pipes),
    }
    if command.view is not None:
        payload["view"] = command.view
    if command.render_mode is not None:
        payload["renderMode"] = command.render_mode
    if command.query is not None:
        payload["query"] = command.query
    return payload


def command_method(
    namespace: str,
    view: str | None,
    args: list[str],
    namespace_index: int,
) -> str:
    if namespace == "search" and view is not None:
        return f"search/{view}"
    if namespace == "agent":
        subcommand = first_positional_after(args, namespace_index) or ""
        return f"agent/{normalize_token(subcommand)}"
    return namespace


def first_positional_after(args: list[str], start: int) -> str | None:
    skip_next = False
    for arg in args[max(0, start + 1) :]:
        if skip_next:
            skip_next = False
            continue
        if option_takes_value(arg):
            skip_next = "=" not in arg
            continue
        if not arg.startswith("-"):
            return arg
    return None


def first_query_positional(
    args: list[str],
    namespace_index: int,
    view: str | None,
) -> str | None:
    skip_next = False
    skipped_view = view is None
    for arg in args[max(0, namespace_index + 1) :]:
        if skip_next:
            skip_next = False
            continue
        if option_takes_value(arg):
            skip_next = "=" not in arg
            continue
        if arg.startswith("-"):
            continue
        token = normalize_token(arg)
        if not skipped_view and token == view:
            skipped_view = True
            continue
        if token in SEARCH_PIPES:
            continue
        return arg
    return None


def option_value(args: list[str], name: str) -> str | None:
    for index, arg in enumerate(args):
        if arg == name:
            try:
                return args[index + 1]
            except IndexError:
                return None
        if arg.startswith(f"{name}="):
            return arg[len(name) + 1 :]
    return None


def option_takes_value(arg: str) -> bool:
    return arg.split("=", 1)[0] in VALUE_OPTIONS


def normalize_token(value: str) -> str:
    token = "".join(
        char.lower()
        for char in value
        if char.isascii() and (char.isalnum() or char in {"-", "_"})
    )
    return token or "unknown"
