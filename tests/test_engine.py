from pathlib import Path

import pytest

from safe_gitignore_builder.engine import (
    TreeVerificationWorkflow,
    build_repo_tree_and_gitignore,
    build_updated_tree_lines,
    scan_repo_tree,
)


def test_scan_is_deterministic_and_skips_internal_directories(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("private", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "app.pyc").write_bytes(b"cache")

    assert scan_repo_tree(tmp_path) == ["src/", "src/app.py"]


def test_rescan_preserves_only_live_safe_markings() -> None:
    current = ["README.md", "src/", "src/app.py", "new.txt"]
    existing = ["!/README.md", "src/", "!/src/app.py", "!/gone.txt"]
    assert build_updated_tree_lines(current, existing) == [
        "new.txt",
        "!/README.md",
        "src/",
        "!/src/app.py",
    ]


def test_compiler_opens_ancestors_and_reignores_unsafe_siblings(tmp_path: Path) -> None:
    tree = tmp_path / "tree.txt"
    output = tmp_path / "candidate.txt"
    tree.write_text("src/\n!/src/app.py\nsrc/private.env\n", encoding="utf-8")
    workflow = TreeVerificationWorkflow(tree, output)
    workflow.run()

    rules = workflow.compile_gitignore_lines()
    assert rules[0] == "# Ignore everything by default"
    assert "/*" in rules
    assert "!/src/" in rules
    assert "!/src/app.py" in rules
    assert "/src/private.env" in rules


def test_fully_safe_folder_compiles_as_a_pair_of_rules(tmp_path: Path) -> None:
    tree = tmp_path / "tree.txt"
    output = tmp_path / "candidate.txt"
    tree.write_text("!/docs/**\n", encoding="utf-8")
    workflow = TreeVerificationWorkflow(tree, output)
    workflow.run()
    rules = workflow.compile_gitignore_lines()
    assert "!/docs/" in rules
    assert "!/docs/**" in rules


def test_end_to_end_writes_only_to_review_workspace(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("hello", encoding="utf-8")
    (target / "secret.env").write_text("do-not-publish", encoding="utf-8")
    workspace = tmp_path / "review"

    result = build_repo_tree_and_gitignore(
        str(target),
        mark_safe="README.md",
        output_dir=str(workspace),
    )

    assert set(path.name for path in workspace.iterdir()) == {
        "project repo tree.txt",
        "project repo tree diff.txt",
        "project generated gitignore.txt",
        "project generated gitignore diff.txt",
    }
    candidate = Path(result["gitignore_output_file"]).read_text(encoding="utf-8")
    assert "!/README.md" in candidate
    assert "secret.env" not in candidate
    assert set(path.name for path in target.iterdir()) == {"README.md", "secret.env"}


def test_marking_unknown_file_fails(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    with pytest.raises(ValueError, match="File not found"):
        build_repo_tree_and_gitignore(
            str(target),
            mark_safe="missing.txt",
            output_dir=str(tmp_path / "review"),
        )


def test_review_output_inside_target_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="outside the target"):
        build_repo_tree_and_gitignore(
            str(target),
            output_dir=str(target / "audit-output"),
        )
    assert not (target / "audit-output").exists()
