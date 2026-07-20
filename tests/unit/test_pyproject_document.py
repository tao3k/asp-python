from __future__ import annotations

from pathlib import Path

import pytest

from python_lang_parser import (
    PythonPyprojectParseError,
    parse_python_pyproject_document,
)


def test_parse_python_pyproject_document_preserves_workspace_members(
    tmp_path: Path,
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "workspace-root"

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]
""".lstrip(),
        encoding="utf-8",
    )

    document = parse_python_pyproject_document(pyproject)

    assert document["tool"]["uv"]["workspace"] == {
        "members": ["packages/*"],
        "exclude": ["packages/experimental"],
    }


@pytest.mark.parametrize("contents", ["[project", "\udcff"])
def test_parse_python_pyproject_document_rejects_invalid_input(
    tmp_path: Path,
    contents: str,
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(contents, encoding="utf-8", errors="surrogatepass")

    with pytest.raises(PythonPyprojectParseError):
        parse_python_pyproject_document(pyproject)


def test_parse_python_pyproject_document_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PythonPyprojectParseError, match="is missing"):
        parse_python_pyproject_document(tmp_path / "pyproject.toml")
