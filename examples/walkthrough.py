"""Review one nested file; inspect generated rules without changing the target."""
import hashlib
import json
import tempfile
from pathlib import Path
from safe_gitignore_builder.engine import build_repo_tree_and_gitignore

with tempfile.TemporaryDirectory(prefix="gitignore-example-") as temporary:
    root = Path(temporary)
    target = root / "target"
    (target / "src").mkdir(parents=True)
    (target / "README.md").write_text("# Synthetic", encoding="utf-8")
    (target / "src/tool.py").write_text("print('demo')\n", encoding="utf-8")
    (target / "src/notes.txt").write_text("Synthetic unreviewed note.", encoding="utf-8")
    def hashes():
        return {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob("*") if p.is_file()}
    before = hashes()
    initial = build_repo_tree_and_gitignore(target=target, output_dir=root / "review")
    denied = Path(initial["gitignore_output_file"]).read_text()
    reviewed = build_repo_tree_and_gitignore(target=target, output_dir=root / "review", mark_safe="src/tool.py")
    rules = Path(reviewed["gitignore_output_file"]).read_text()
    repeated = build_repo_tree_and_gitignore(target=target, output_dir=root / "review")
    assert Path(repeated["gitignore_output_file"]).read_text() == rules
    assert before == hashes() and not (target / ".gitignore").exists()
    print(json.dumps({"initial_rules": denied, "reviewed_rules": rules, "review_survives_rescan": True, "target_unchanged": True}, indent=2))
