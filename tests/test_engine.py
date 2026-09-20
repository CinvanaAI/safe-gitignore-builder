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
    assert "/src/*" in rules


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


def test_new_siblings_stay_ignored_by_real_git_after_approval(tmp_path: Path) -> None:
    import shutil
    import subprocess
    if not shutil.which("git"):
        pytest.skip("Git is required for the integration check")
    target = tmp_path / "project"
    target.mkdir()
    (target / "src").mkdir()
    (target / "src" / "file[1].py").write_text("pass", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", str(target)], check=True)
    result = build_repo_tree_and_gitignore(str(target), "src/file[1].py", str(tmp_path / "review"))
    (target / ".gitignore").write_text(Path(result["gitignore_output_file"]).read_text(), encoding="utf-8")
    # These appear after review, before any rescan.
    (target / "src" / "new-secret.txt").write_text("synthetic", encoding="utf-8")
    (target / "src" / "file1.py").write_text("unreviewed", encoding="utf-8")
    for name, expected in (("src/file[1].py", 1), ("src/new-secret.txt", 0), ("src/file1.py", 0)):
        result = subprocess.run(["git", "-C", str(target), "check-ignore", "--no-index", "-q", name])
        assert result.returncode == expected, name
    rescanned = build_repo_tree_and_gitignore(str(target), output_dir=str(tmp_path / "review"))
    tree = Path(rescanned["tree_file"]).read_text()
    assert "!/src/file[1].py" in tree and "!/src/**" not in tree


@pytest.mark.parametrize("name", ["!", "#notes", " leading"])
def test_reserved_inventory_names_do_not_widen_a_git_candidate(tmp_path: Path, name: str) -> None:
    import shutil
    import subprocess
    if not shutil.which("git"):
        pytest.skip("Git is required for the integration check")
    target = tmp_path / "project"
    target.mkdir()
    subprocess.run(["git", "init", "--quiet", str(target)], check=True)
    result = build_repo_tree_and_gitignore(str(target), output_dir=str(tmp_path / "review"))
    candidate = Path(result["gitignore_output_file"])
    before = candidate.read_bytes()
    reserved = target / name
    reserved.mkdir()
    (reserved / "later.txt").write_text("unreviewed", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported path name"):
        build_repo_tree_and_gitignore(str(target), output_dir=str(tmp_path / "review"))
    assert candidate.read_bytes() == before
    (target / ".gitignore").write_bytes(before)
    (target / "later.txt").write_text("new unreviewed root file", encoding="utf-8")
    assert subprocess.run(["git", "-C", str(target), "check-ignore", "--no-index", "-q", "later.txt"]).returncode == 0


@pytest.mark.parametrize("name", ["file\n!/leak.txt", "file\rname", "file\tname", "name ", "docs/**", "a\\b"])
def test_inventory_format_rejects_unrepresentable_names(name):
    from safe_gitignore_builder.engine import _validate_inventory_path
    with pytest.raises(ValueError, match="Unsupported path name"):
        _validate_inventory_path(name)
