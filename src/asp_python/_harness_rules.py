"""Render source-embedded Python harness rule fixtures."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

_HARNESS_RULES_RESOURCE = "harness-rules.md"


def python_harness_rules_markdown() -> str:
    """Return the source-embedded harness rule list."""

    return (
        files(__package__).joinpath(_HARNESS_RULES_RESOURCE).read_text(encoding="utf-8")
    )


def render_python_harness_rules_markdown() -> str:
    """Render the source-embedded Python harness rules as markdown."""

    output = [
        "# asp-python",
        "",
        "## Harness Rules",
        "",
        "Generated from embedded `src/asp_python/harness-rules.md`.",
        "",
    ]
    for line in python_harness_rules_markdown().splitlines():
        if item := line.removeprefix("- "):
            if ": " in item:
                rule_id, sentence = item.split(": ", 1)
                output.append(f"- **{rule_id}**: {sentence}")
    return "\n".join(output) + "\n"


def write_python_harness_rules_to_unit_tests(unit_test_dir: Path) -> Path:
    """Write the generated harness rules into a downstream unit test directory."""

    output_path = unit_test_dir / "harness-rules.generated.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_python_harness_rules_markdown(), encoding="utf-8")
    return output_path
