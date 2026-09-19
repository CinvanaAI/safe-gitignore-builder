# Origin

This repository comes from a Workbench tool built to solve a publication-safety problem: start with everything ignored, inspect the actual repository tree, and explicitly mark only reviewed paths as safe.

The original working folder included separate tree and compiler scripts, a combined workflow, and generated census/diff files—including one tree report around 19 MB. This extraction keeps the combined authored workflow, packages it as a command, adds an explicit external output directory, supplies synthetic tests, and excludes project-specific generated reports.

