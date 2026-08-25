import python_lang_parser


def test_pyproject_document_api_is_publicly_exported() -> None:
    expected = {
        "PythonPyprojectParseError",
        "parse_python_pyproject_document",
    }

    assert expected <= set(python_lang_parser.__all__)
    for name in expected:
        assert getattr(python_lang_parser, name) is not None
