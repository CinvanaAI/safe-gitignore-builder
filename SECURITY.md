# Security boundary

This tool reduces accidental publication risk; it does not prove a repository is safe.

- The target is scanned read-only. Review artifacts must be written outside it, and symbolic links are excluded from the inventory.
- A path marked safe is a human decision. The compiler does not inspect file contents, licenses, generated artifacts, credentials, personal data, or Git history.
- Review the candidate rules and both diffs before copying anything into the target.
- Re-run the inventory after files change. New paths return as unsafe, but edited content at an already approved path remains approved until a human revisits it.
- `.gitignore` affects future untracked-file selection. It does not remove files or secrets already committed, staged, cached, or present in prior history.
- Keep each target's persistent review artifacts in a clearly named directory. Reusing one output location for unrelated targets with the same folder name can mix review state.

Use a separate secret scanner, license/material review, and Git-history review before publication.
