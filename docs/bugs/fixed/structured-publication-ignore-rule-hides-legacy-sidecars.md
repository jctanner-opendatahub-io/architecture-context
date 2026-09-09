# F-P4-1 — publication ignore rule hides new legacy sidecars

Status: open — discovered in independent P4 cycle1 review.

Blocking SC-21/23. `.gitignore` ignores architecture/*/*/.generation/, including future legacy SURFACE_COVERAGE.json and SOURCE_READ_JUSTIFICATIONS.json.898 existing tracked files match the broad rule; new legacy files would be omitted from git add, losing history on fresh clones. Narrow private structured state exclusions and retain legacy tracking. Verify git check-ignore against both private and legacy paths.

Evidence: [review report](../../../logs/structured-component-assembly/20260908-publication/review-report.md),
reviewer Fable/high session a5d91853-a159-43d6-8187-97ba233134c9,
2026-09-09T01:12:18Z. No live calls or actual rate limits.

## Fixed — P4 independently accepted 2026-09-09 UTC

Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655 returnedP4 PASS,
confirming this bug's acceptance criteria on555verifiedsourcefiles. Independent
fullPython1320pass10skip, readonlyCLI/treeidentity andactualGit tests pass;
cycle1query/consumer/reuseevidence retainedbyhash. [Review report](../../../logs/structured-component-assembly/20260909-publication-repair/review-report.md).
Offline implementation acceptance only; liveadoption separate.
