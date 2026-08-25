from __future__ import annotations

from python_lang_project_harness._cli_args import help_text


def test_public_cli_identity_is_asp_python_without_legacy_aliases() -> None:
    rendered = help_text()

    assert rendered.startswith("asp-python ")
    assert "asp-python search" in rendered
    assert "asp-python check" in rendered
    assert "py-harness" not in rendered
