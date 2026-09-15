"""Render source-embedded ASP Python rule fixtures."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

_ASP_RULES_RESOURCE = "asp-rules.md"


def asp_python_rules_markdown() -> str:
    """Return the source-embedded ASP Python rule list."""

    return files(__package__).joinpath(_ASP_RULES_RESOURCE).read_text(encoding="utf-8")


def render_asp_python_rules_markdown() -> str:
    """Render the source-embedded ASP Python rules as markdown."""

    output = [
        "# asp-python",
        "",
        "## ASP Python Rules",
        "",
        "Generated from embedded `src/asp_python/asp-rules.md`.",
        "",
    ]
    for line in asp_python_rules_markdown().splitlines():
        if item := line.removeprefix("- "):
            if ": " in item:
                rule_id, sentence = item.split(": ", 1)
                output.append(f"- **{rule_id}**: {sentence}")
    return "\n".join(output) + "\n"


def write_asp_python_rules_to_unit_tests(unit_test_dir: Path) -> Path:
    """Write the generated ASP Python rules into a downstream unit test directory."""

    output_path = unit_test_dir / "asp-rules.generated.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_asp_python_rules_markdown(), encoding="utf-8")
    return output_path
