# Safe Gitignore Builder

An allowlist-style `.gitignore` compiler for reviewing messy repositories before publication.

Most generated `.gitignore` files begin with a list of known junk. This tool reverses the burden of proof:

1. Ignore everything.
2. Inventory the repository.
3. Mark reviewed files as safe.
4. Generate the minimum unignore rules required to expose those files.
5. Re-ignore unsafe siblings inside partially opened folders.

The tool never writes `.gitignore` into the target repository. It requires the review directory to be outside that target, then writes an inventory, generated candidate, and unified diff reports there.

## Install

```powershell
python -m pip install -e ".[test]"
```

## Start a review

```powershell
safe-gitignore --target C:\path\to\project --output-dir .\audit-output
```

This creates four files named after the target:

- `<repo> repo tree.txt`
- `<repo> repo tree diff.txt`
- `<repo> generated gitignore.txt`
- `<repo> generated gitignore diff.txt`

Unreviewed entries in the tree are plain paths. Mark one file safe by rerunning:

```powershell
safe-gitignore --target C:\path\to\project --output-dir .\audit-output --mark-safe README.md
```

Safe files are stored as `!/path/to/file` in the persistent tree. Later scans preserve those decisions while removing paths that no longer exist and adding newly discovered paths as unsafe.

After review, inspect the generated candidate and copy it into the target repository yourself. That final manual step is deliberate.

## Safety properties

- Default-deny output begins with `/*`.
- `.git`, `__pycache__`, and symbolic links are excluded from inventory.
- Marking a nested file opens only the necessary ancestor folders.
- Unsafe siblings inside an opened folder are explicitly re-ignored.
- The target repository is read-only to this program.
- Generated files and diffs live in the chosen review directory.

## Important limit

A correct `.gitignore` prevents new accidental additions; it does not remove secrets already committed to Git history. Review Git history separately before publication.

## Test

```powershell
python -m pytest
```

See `ORIGIN.md` for the extraction boundary. Owned code is available under MIT; see LICENSE.md.

See `SECURITY.md` for the boundary this tool does and does not provide.
