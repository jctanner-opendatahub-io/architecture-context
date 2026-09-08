# Component reuse fingerprint measurement

Candidate fact-match rates between adjacent version checkouts, produced by
running the working-tree `bin/arch-analyzer` on both checkouts and comparing
normalized output. See `docs/plans/structured-component-assembly.md`, sections
"Review response: reuse premise measured" and the consensus record that follows.

These are **candidate** matches. Supporting source reads, search scope,
overlays, configuration, and synthesis contract were not compared, so the
numbers are upper bounds on verified synthesis reuse.

- `rhoai-3.6-ea.1-to-ea.2.json`: per-component commits, tree hashes, semantic
  fingerprints, per-tier match flags, differing categories, normalization rules,
  analyzer revision state, and totals.
- `compare.py`: the scoring script. It expects a directory with `ea1/` and
  `ea2/` subdirectories of `arch-analyzer extract` output named
  `<org>__<repo>.json`.

Analyzer revision for the recorded run: repository HEAD `39209078` with 11
uncommitted files under `src/arch-analyzer/`; reproduce only from a committed
analyzer revision.
