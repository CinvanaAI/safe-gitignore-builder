# Safe Gitignore Builder

Review a messy source tree and generate an allowlist-style ignore candidate that exposes only explicitly approved files.

## See it work

**Input:** A synthetic target with README.md, src/tool.py, and unreviewed src/notes.txt.

**Result:** A default-deny candidate that opens src/tool.py, keeps src/notes.txt ignored, and leaves all target bytes unchanged.

[Read the captured output](examples/result.txt) | [Inspect the example](examples/walkthrough.py)

Python 3.11 or newer. From the repository root:

```sh
python -m pip install -e .
python -m examples.walkthrough
```

The example uses synthetic material and runs offline. The captured output comes from executing this example, not a hand-written mockup.

## How it works

The tool inventories a target, retains explicit reviewed-file decisions, and compiles only the required ancestor unignore rules. Unreviewed siblings inside an opened folder are re-ignored. The example approves one nested file and verifies that the decision survives a rescan.

Implementation: [src/safe_gitignore_builder/engine.py](src/safe_gitignore_builder/engine.py), [tests/test_engine.py](tests/test_engine.py), [README.md](README.md).

## Limits

It writes review artifacts outside the target and never installs the generated .gitignore. Ignore rules do not remove tracked files, rewrite history, or establish that an approved file is safe; that remains the reviewer's decision.

[Reference and CLI details](docs/REFERENCE.md) | [Origin](ORIGIN.md) | [MIT license](LICENSE.md)
