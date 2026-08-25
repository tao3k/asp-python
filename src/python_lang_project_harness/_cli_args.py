"""Argument parsing helpers for the Python harness CLI."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._model import PythonHarnessConfig
    from ._tree_sitter_query_predicates import SyntaxQueryPredicate


@dataclass(slots=True)
class ProtocolArgs:
    command: str
    view: str | None = None
    action: str | None = None
    client: str | None = None
    hook_event: str | None = None
    query: str | None = None
    item_query: str | None = None
    project_root: Path | None = None
    package_path: Path | None = None
    workspace: bool = False
    owner_path: str | None = None
    dependency: str | None = None
    selector: str | None = None
    catalog: str | None = None
    flow_lite_where: str | None = None
    tree_sitter_query: str | None = None
    asp_syntax_query_captures: tuple[str, ...] = ()
    asp_syntax_query_node_types: tuple[str, ...] = ()
    asp_syntax_query_fields: tuple[str, ...] = ()
    asp_syntax_query_predicates: tuple[SyntaxQueryPredicate, ...] = ()
    packet_path: str | None = None
    query_set: tuple[str, ...] = ()
    pipes: tuple[str, ...] = ()
    json: bool = False
    names_only: bool = False
    source_version: str = "worktree"
    render_mode: str | None = None
    error: str | None = None

    @classmethod
    def parse(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs | None:
        command = args[0] if args else None
        if command == "search":
            return cls._parse_search(args[1:])
        if command == "query":
            return cls._parse_query(args[1:])
        if command == "check":
            return cls._parse_check(args[1:])
        if command == "evidence":
            return cls._parse_evidence(args[1:])
        if command == "agent":
            return cls._parse_agent(args[1:])
        if command == "ast-patch":
            return cls._parse_ast_patch(args[1:])
        return None

    @classmethod
    def _parse_search(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        if args and args[0] in {"--help", "-h"}:
            return cls("help")
        from ._semantic_search_cli import parse_semantic_search_args

        parsed = parse_semantic_search_args(args)
        if parsed.error is not None:
            return cls("error", error=parsed.error)
        return cls(
            "search",
            view=parsed.view,
            query=parsed.query,
            item_query=parsed.item_query,
            owner_path=parsed.owner_path,
            dependency=parsed.dependency,
            query_set=parsed.query_set,
            project_root=parsed.project_root,
            package_path=parsed.package_path,
            workspace=parsed.workspace,
            pipes=parsed.pipes,
            json=parsed.json,
            render_mode=parsed.render_mode,
        )

    @classmethod
    def _parse_query(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        from ._cli_query_args import parse_query_args

        return parse_query_args(cls, args)

    @classmethod
    def _parse_ast_patch(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        mode = args[0] if args else None
        if mode in {"--help", "-h"}:
            return cls("help")
        if mode != "dry-run":
            return cls("error", error="expected ast-patch dry-run")

        packet_path: str | None = None
        positionals: list[Path] = []
        index = 1
        while index < len(args):
            arg = args[index]
            if arg == "--packet":
                value = args[index + 1] if index + 1 < len(args) else None
                if value is None or (value.startswith("-") and value != "-"):
                    return cls("error", error="--packet requires a path or -")
                packet_path = value
                index += 2
                continue
            if arg.startswith("-"):
                return cls("error", error=f"unknown ast-patch option: {arg}")
            positionals.append(Path(arg))
            index += 1
        if packet_path is None:
            return cls("error", error="--packet requires a path or -")
        if len(positionals) > 1:
            return cls("error", error="expected at most one PROJECT_ROOT argument")
        return cls(
            "ast-patch",
            packet_path=packet_path,
            project_root=positionals[0] if positionals else None,
        )

    @classmethod
    def _parse_check(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        json_output = False
        positionals: list[str] = []
        for arg in args:
            if arg == "--json":
                json_output = True
            elif arg in {"--changed", "--full"}:
                continue
            elif arg in {"--help", "-h"}:
                return cls(
                    "error",
                    error="usage: asp-python check [--changed | --full] [--json] [PROJECT_ROOT]",
                )
            elif arg.startswith("-"):
                return cls("error", error=f"unknown check option: {arg}")
            else:
                positionals.append(arg)
        if len(positionals) > 1:
            return cls("error", error="expected at most one PROJECT_ROOT argument")
        return cls(
            "check",
            project_root=None if not positionals else Path(positionals[0]),
            json=json_output,
        )

    @classmethod
    def _parse_evidence(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        action = args[0] if args else None
        if action in {"--help", "-h"}:
            return cls("help")
        if action not in {"graph", "analyze", "analysis"}:
            return cls("error", error="expected evidence <graph|analyze>")
        json_output = False
        positionals: list[str] = []
        for arg in args[1:]:
            if arg == "--json":
                json_output = True
            elif arg in {"--help", "-h"}:
                return cls("help")
            elif arg.startswith("-"):
                return cls("error", error=f"unknown evidence option: {arg}")
            else:
                positionals.append(arg)
        if len(positionals) > 1:
            return cls("error", error="expected at most one PROJECT_ROOT argument")
        return cls(
            "evidence",
            action="analyze" if action == "analysis" else action,
            project_root=None if not positionals else Path(positionals[0]),
            json=json_output,
        )

    @classmethod
    def _parse_agent(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        action = args[0] if args else "doctor"
        if action in {"install", "hook"}:
            replacement = (
                "asp hook install --client codex"
                if action == "install"
                else "asp hook <event> --client codex"
            )
            return cls(
                "error",
                error=f"asp-python agent {action} moved to asp; use `{replacement}`",
            )
        if action == "guide":
            return cls._parse_agent_guide(args[1:])
        if action != "doctor":
            return cls("error", error=f"unknown agent action: {action}")
        client: str | None = None
        hook_event: str | None = None
        json_output = False
        positionals: list[str] = []
        index = 1
        while index < len(args):
            arg = args[index]
            if arg == "--json":
                json_output = True
            elif arg == "--client":
                value = _optional_arg(args, index + 1)
                if value is None:
                    return cls("error", error="--client requires a client name")
                if value != "codex":
                    return cls("error", error=f"unsupported agent client: {value}")
                client = value
                index += 1
            elif arg in {"--help", "-h"}:
                continue
            elif arg.startswith("-"):
                return cls("error", error=f"unknown agent option: {arg}")
            elif action == "hook" and hook_event is None:
                hook_event = arg
            else:
                positionals.append(arg)
            index += 1
        if len(positionals) > 1:
            return cls("error", error="expected at most one PROJECT_ROOT argument")
        return cls(
            "agent",
            action=action,
            client=client,
            hook_event=hook_event,
            project_root=None if not positionals else Path(positionals[0]),
            json=json_output,
        )

    @classmethod
    def _parse_agent_guide(cls, args: list[str] | tuple[str, ...]) -> ProtocolArgs:
        positionals: list[str] = []
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == "--client":
                value = _optional_arg(args, index + 1)
                if value is None:
                    return cls("error", error="--client requires a client name")
                index += 1
            elif arg in {"--help", "-h"}:
                pass
            elif arg.startswith("-"):
                return cls("error", error=f"unknown agent option: {arg}")
            else:
                positionals.append(arg)
            index += 1
        if len(positionals) > 1:
            return cls("error", error="expected at most one PROJECT_ROOT argument")
        return cls(
            "agent",
            action="guide",
            project_root=None if not positionals else Path(positionals[0]),
        )


@dataclass(slots=True)
class CliOptions:
    json: bool = False
    agent_snapshot: bool = False
    help: bool = False
    include_tests: bool | None = None
    source_dir_values: list[str] = field(default_factory=list)
    test_dir_values: list[str] = field(default_factory=list)
    extra_path_values: list[str] = field(default_factory=list)
    disabled_rule_values: list[str] = field(default_factory=list)
    blocking_rule_values: list[str] = field(default_factory=list)
    paths: list[Path] = field(default_factory=list)

    @classmethod
    def parse(cls, args: list[str] | tuple[str, ...]) -> CliOptions:
        options = cls()
        positional_only = False
        index = 0
        while index < len(args):
            arg = args[index]
            index += 1
            if positional_only:
                options.paths.append(Path(arg))
                continue
            match arg:
                case "--":
                    positional_only = True
                case "--json":
                    options.json = True
                case "--agent-snapshot":
                    options.agent_snapshot = True
                case "--no-tests":
                    options.include_tests = False
                case "--source-dir":
                    options.source_dir_values.append(
                        _option_value(args, index, "--source-dir")
                    )
                    index += 1
                case "--test-dir":
                    options.test_dir_values.append(
                        _option_value(args, index, "--test-dir")
                    )
                    index += 1
                case "--extra-path":
                    options.extra_path_values.append(
                        _option_value(args, index, "--extra-path")
                    )
                    index += 1
                case "--disable-rule":
                    options.disabled_rule_values.append(
                        _option_value(args, index, "--disable-rule")
                    )
                    index += 1
                case "--block-rule":
                    options.blocking_rule_values.append(
                        _option_value(args, index, "--block-rule")
                    )
                    index += 1
                case "--help" | "-h":
                    options.help = True
                case value if value.startswith("-"):
                    raise ValueError(f"unknown option: {value}")
                case value:
                    options.paths.append(Path(value))
        if len(options.paths) > 1:
            raise ValueError("expected at most one PROJECT_ROOT argument")
        if options.json and options.agent_snapshot:
            raise ValueError("--json and --agent-snapshot are mutually exclusive")
        return options

    def project_root(self, cwd: Path | None) -> Path:
        if self.paths:
            return self.paths[0]
        if cwd is not None:
            return cwd
        return Path.cwd()

    @property
    def source_dir_names(self) -> tuple[str, ...] | None:
        """Return explicit source roots, when the CLI supplied any."""

        if not self.source_dir_values:
            return None
        return tuple(self.source_dir_values)

    @property
    def test_dir_names(self) -> tuple[str, ...] | None:
        """Return explicit test roots, when the CLI supplied any."""

        if not self.test_dir_values:
            return None
        return tuple(self.test_dir_values)

    @property
    def extra_path_names(self) -> tuple[str, ...] | None:
        """Return explicit extra project paths, when the CLI supplied any."""

        if not self.extra_path_values:
            return None
        return tuple(self.extra_path_values)

    def harness_config(self, project_root: Path) -> PythonHarnessConfig | None:
        """Return CLI policy config when rule-level options were supplied."""

        if not self.disabled_rule_values and not self.blocking_rule_values:
            return None
        from ._model import PythonHarnessConfig
        from ._project_config import read_python_project_harness_config

        base_config = read_python_project_harness_config(project_root)
        config = base_config if base_config is not None else PythonHarnessConfig()
        return replace(
            config,
            disabled_rule_ids=(
                frozenset(self.disabled_rule_values)
                if self.disabled_rule_values
                else config.disabled_rule_ids
            ),
            blocking_rule_ids=(
                frozenset(self.blocking_rule_values)
                if self.blocking_rule_values
                else config.blocking_rule_ids
            ),
        )


def help_text() -> str:
    return (
        "asp-python — Python semantic search and project harness\n\n"
        "Usage:\n"
        "  asp-python search <view> ... [--json] [--package PATH] [--workspace <workspace-root>]\n"
        "  asp python query --selector <exact-structural-selector> --projection <source|callable-skeleton> --workspace <workspace-root>\n"
        "  asp-python query --catalog flow-lite --where 'source.call=NAME sink.constructs=TYPE scope.fn=FUNCTION' [--json] [--workspace <workspace-root>]\n"
        "  asp-python check [--changed | --full] [--json]\n"
        "  asp-python evidence graph [--json] [PROJECT_ROOT]\n"
        "  asp-python evidence analyze [--json] [PROJECT_ROOT]\n"
        "  asp-python ast-patch dry-run --packet <semantic-ast-patch.json|->\n"
        "  asp-python agent doctor [--json]\n"
        "  asp-python agent guide\n"
        "  asp-python [--json | --agent-snapshot] [--no-tests] "
        "[--source-dir DIR] [--test-dir DIR] [--extra-path PATH] "
        "[--disable-rule RULE_ID] [--block-rule RULE_ID] [PROJECT_ROOT]\n\n"
        "SEARCH VIEWS\n"
        "  search workspace          Workspace package/router index\n"
        "  search prime              Project reasoning-tree map\n"
        "  search owner <path>       Owner graph slice\n"
        "  search owner <path> items --query <symbol|a|b>\n"
        "                             Parser-owned structural selector discovery\n"
        "  search dependency <pkg>   Dependency manifest and local import usage\n"
        "  search deps <pkg[@ver][::api]>\n"
        "                             Versioned dependency API usage evidence\n"
        "  search api <query>        Parser-owned public API facts\n"
        "  search public-external-types <pkg>\n"
        "                             Public API type surfaces exposing a dependency\n"
        "  search symbol <name>      Symbol/export definitions\n"
        "  search callsite <name>    Parser-owned function and method callsites\n"
        "  search import <query>     Import owner edges\n"
        "  search tests <owner>      Tests that import an owner\n"
        "  search lexical --query <term> --query <term>\n"
        "                             Lexical owner/source-text candidates\n"
        "  search lexical --query <term> --query <term> owner tests\n"
        "                             Minimal final-only lexical -> owner -> tests pipe\n"
        "  search reasoning owner-tests --owner <path>\n"
        "                             Typed graph entry returning covering tests, entrypoints, and fixtures\n"
        "  search reasoning owner-query --owner <path> --query <symbol>\n"
        "                             Typed graph entry returning owner items, tests, and dependency usage\n"
        "  search reasoning query-deps --query <symbol> --dependency <pkg>\n"
        "                             Typed graph entry returning owners, imports, and usage tests\n"
        "  search ingest             Detect stdin shape and group hits by owner\n\n"
        "QUERY\n"
        "  asp python query --selector <python-structural-selector> --projection source --workspace <workspace-root>\n"
        "                             Exact source materialization through ASP authority\n"
        "  asp python query --selector <python-structural-selector> --projection callable-skeleton --workspace <workspace-root>\n"
        "                             Typed callable skeleton materialization through ASP authority\n\n"
        "  query --catalog flow-lite --where 'source.call=NAME sink.constructs=TYPE scope.fn=FUNCTION'\n"
        "                             Flow-lite ABI compatibility surface; Python executor is not enabled yet\n\n"
        "CHECK\n"
        "  check --changed           Fast lane alias; currently delegates to project check\n"
        "  check --full              Full project harness check\n"
        "  check --json              Structured PythonHarnessReport JSON\n\n"
        "EVIDENCE\n"
        "  evidence graph --json     Portable semantic-evidence-graph packet\n"
        "  evidence analyze --json   Graph-turbo request for evidence-quality ranking\n\n"
        "AST PATCH\n"
        "  ast-patch dry-run --packet <path|->\n"
        "                             Provider-native structural patch receipt; never mutates files\n\n"
        "AGENT\n"
        "  agent doctor              Print semantic-language provider readiness\n"
        "  agent doctor --json       Semantic language registry document\n\n"
        "  agent guide               Print command-line search flow guide\n\n"
        "  Hook install/runtime is owned by asp in the root toolchain.\n\n"
        "DIRECT CHECK\n"
        "The no-command form still runs the default package-level Python harness.\n\n"
        "Compact text is the default output for humans and repair-oriented agents.\n"
        "Use --json to emit the structured PythonHarnessReport JSON shape.\n"
        "Use --agent-snapshot to emit parser facts for project repair agents.\n"
        "Repeat --source-dir or --test-dir to customize policy root classification.\n"
        "Repeat --extra-path to include external project paths.\n"
        "Repeat --disable-rule or --block-rule to customize policy by rule id.\n"
        "\nEXAMPLES\n"
        "  asp-python search workspace .\n"
        "  asp-python search prime .\n"
        "  asp-python search public-external-types pytest .\n"
        "  asp-python search callsite PythonSemanticSearchOptions .\n"
        "  asp python search lexical --query PythonSemanticSearchOptions --query owner --workspace .\n"
        "  asp-python search reasoning owner-tests --owner src/python_lang_project_harness/_cli.py .\n"
        "  asp-python search reasoning owner-query --owner src/python_lang_project_harness/_cli.py --query run_cli .\n"
        "  asp-python search reasoning query-deps --query Session --dependency requests .\n"
        "  asp python query --selector 'python://src/python_lang_project_harness/_cli.py#item/function/run_cli' --projection source --workspace .\n"
        "  asp-python query --catalog flow-lite --where 'source.call=payload sink.constructs=Action scope.fn=collect' .\n"
        "  asp python search lexical --query PythonSemanticSearchOptions --workspace . --view seeds\n"
        "  asp-python check --full .\n"
        "  asp-python evidence graph --json .\n"
        "  asp-python evidence analyze --json .\n"
        "  asp-python agent doctor --json .\n"
        "  asp-python agent guide\n"
    )


def _optional_arg(args: list[str] | tuple[str, ...], index: int) -> str | None:
    if index >= len(args):
        return None
    value = args[index]
    if value.startswith("-"):
        return None
    return value


def _option_value(
    args: list[str] | tuple[str, ...],
    index: int,
    option_name: str,
) -> str:
    if index >= len(args):
        raise ValueError(f"missing value for {option_name}")
    value = args[index]
    if value.startswith("-"):
        raise ValueError(f"missing value for {option_name}")
    return value
