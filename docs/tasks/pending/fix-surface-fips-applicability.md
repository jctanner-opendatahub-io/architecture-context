# Task: Fix Surface FIPS Applicability

Status: pending, after the worktree checkpoint.

Follow step 1 of the [plan](../../plans/architecture-surface-coverage.md) and the
[open bug](../../bugs/open/surface-inventory-nominates-empty-fips-category.md).
Require an explicit applicability basis, not merely an empty coverage category.
Preserve uncertain applicability and distinguish build evidence from runtime
compliance; zero facts do not prove not-applicable.

Acceptance: positive, empty, ambiguous, and explicit-negative tests; independent
review; reproducible audit nomination deltas; no generated-document edits or
enforcement changes. Close the bug only after verification.
