from __future__ import annotations

from pathlib import Path

from snapshot_support import assert_snapshot

from python_lang_parser import (
    PythonDiagnosticSeverity,
    PythonModuleReport,
    PythonProjectEntryPoint,
    PythonProjectImportName,
    PythonProjectMetadata,
    PythonProjectScript,
    SourceLocation,
    parse_python_source,
)
from python_lang_project_harness import (
    PythonHarnessFinding,
    PythonHarnessReport,
    PythonProjectHarnessScope,
    render_python_lang_harness,
    render_python_lang_harness_json,
    render_python_reasoning_tree,
)


def test_compact_text_render_matches_snapshot() -> None:
    rendered = render_python_lang_harness(_snapshot_report())

    assert_snapshot("python_project_harness_compact_text", rendered)


def test_json_render_matches_snapshot() -> None:
    rendered = render_python_lang_harness_json(_snapshot_report())

    assert_snapshot("python_project_harness_json", rendered)


def test_reasoning_tree_render_matches_snapshot() -> None:
    rendered = render_python_reasoning_tree(_reasoning_tree_snapshot_report())

    assert_snapshot("python_project_reasoning_tree", rendered)


def test_reasoning_tree_render_uses_project_relative_paths(tmp_path: Path) -> None:
    src = tmp_path / "src"
    package = src / "pkg"
    package.mkdir(parents=True)
    report = PythonHarnessReport(
        modules=(
            parse_python_source(
                '"""Package docs."""\n\nVALUE = 1\n',
                path=package / "__init__.py",
            ),
        ),
        findings=(),
        root_paths=(str(tmp_path),),
        project_resolution=PythonProjectHarnessScope(
            project_root=tmp_path,
            project_metadata=PythonProjectMetadata(
                project_root=tmp_path,
                pyproject_path=tmp_path / "pyproject.toml",
                has_project_table=True,
                has_build_system_table=True,
                project_name="relative-package",
                requires_python=">=3.12",
                build_backend="hatchling.build",
                build_requires=("hatchling",),
                wheel_packages=("src/pkg",),
                package_roots=(package,),
                import_names=(
                    PythonProjectImportName(
                        name="pkg",
                        namespace=("pkg",),
                        source_value="pkg",
                    ),
                ),
            ),
            project_paths=(tmp_path,),
            source_paths=(src,),
            test_paths=(),
        ),
    )

    rendered = render_python_reasoning_tree(report)

    assert str(tmp_path) not in rendered
    assert rendered.startswith("[tree] . python\n")
    assert "package-roots=src/pkg" in rendered
    assert "src/pkg/__init__.py" in rendered


def test_compact_text_render_uses_project_relative_finding_paths(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    report = PythonHarnessReport(
        modules=(),
        findings=(
            PythonHarnessFinding(
                rule_id="PY-MOD-R002",
                pack_id="python.modern_design",
                severity=PythonDiagnosticSeverity.WARNING,
                title="Library module uses bare print",
                summary="library.py calls bare print().",
                location=SourceLocation(str(src / "library.py"), 3, 4),
                requirement="Use a logger instead of bare `print`.",
                source_line='    print("debug")',
                label="replace bare print with a project-owned reporting surface",
            ),
        ),
        root_paths=(str(tmp_path),),
        project_resolution=PythonProjectHarnessScope(
            project_root=tmp_path,
            project_paths=(tmp_path,),
            source_paths=(src,),
            test_paths=(),
        ),
    )

    rendered = render_python_lang_harness(report)

    assert str(tmp_path) not in rendered
    assert "path=src/library.py line=3 column=5" in rendered


def _snapshot_report() -> PythonHarnessReport:
    source_path = "$TEMP/src/service.py"
    return PythonHarnessReport(
        modules=(
            PythonModuleReport(
                path=source_path,
                module_docstring="Service helpers.",
            ),
        ),
        findings=(
            PythonHarnessFinding(
                rule_id="PY-MOD-R002",
                pack_id="python.modern_design",
                severity=PythonDiagnosticSeverity.WARNING,
                title="Library module uses bare print",
                summary="$TEMP/src/service.py calls bare print().",
                location=SourceLocation(source_path, 5, 4),
                requirement=(
                    "Use a logger, returned value, or explicit test assertion "
                    "instead of bare `print` in library modules."
                ),
                source_line='    print("debug")',
                label="replace bare print with a project-owned reporting surface",
                labels={"domain": "modern-python", "language": "python"},
            ),
        ),
        root_paths=("$TEMP/src", "$TEMP/tests"),
    )


def _reasoning_tree_snapshot_report() -> PythonHarnessReport:
    root = Path("$TEMP")
    src = root / "src"
    return PythonHarnessReport(
        modules=(
            parse_python_source(
                '"""Domain package owner."""\n\nfrom .service import build\n\n__all__ = ("build",)\n',
                path=src / "pkg" / "domain" / "__init__.py",
            ),
            parse_python_source(
                '"""Service leaf."""\n\n\ndef build(value: int) -> int:\n    return value\n',
                path=src / "pkg" / "domain" / "service.py",
            ),
            parse_python_source(
                '"""Model leaf."""\n\nfrom .service import build\n\n\nclass Model:\n    pass\n',
                path=src / "pkg" / "domain" / "models.py",
            ),
        ),
        findings=(),
        root_paths=(str(root),),
        project_resolution=PythonProjectHarnessScope(
            project_root=root,
            project_metadata=PythonProjectMetadata(
                project_root=root,
                pyproject_path=root / "pyproject.toml",
                has_project_table=True,
                has_build_system_table=True,
                project_name="snapshot-package",
                requires_python=">=3.12",
                build_backend="hatchling.build",
                build_requires=("hatchling",),
                wheel_packages=("src/pkg",),
                package_roots=(src / "pkg",),
                import_names=(
                    PythonProjectImportName(
                        name="pkg",
                        namespace=("pkg",),
                        source_value="pkg",
                    ),
                ),
                scripts=(
                    PythonProjectScript(
                        name="snapshot-cli",
                        target="pkg.cli:main",
                        kind="console",
                    ),
                ),
                entry_points=(
                    PythonProjectEntryPoint(
                        group="pytest11",
                        name="snapshot",
                        target="pkg.pytest_plugin",
                    ),
                ),
            ),
            project_paths=(root,),
            source_paths=(src,),
            test_paths=(),
        ),
    )
