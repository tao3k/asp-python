from __future__ import annotations

from asp_python._cli_args import help_text


def test_public_cli_identity_is_asp_python() -> None:
    rendered = help_text()

    assert rendered.startswith("asp-python ")
    assert "asp-python search" in rendered
