# F-P4-2 — architecture lint repairs stale output instead of failing

Status: open — discovered in independent P4 cycle1 review.

Blocking SC-17/21. Actual linter invocation on stale Markdown under a copied valid marker exits0 and rewrites the file because accepted_publications uses repair_markdown=True; it also creates recovery lock directories. Lint must be read-only and fail on stale/tampered derivatives. Test actual CLI, valid and invalid documents, unchanged bytes and no new directories. Existing import bug stays open until this passes.

Evidence: [review report](../../../logs/structured-component-assembly/20260908-publication/review-report.md),
reviewer Fable/high session a5d91853-a159-43d6-8187-97ba233134c9,
2026-09-09T01:12:18Z. No live calls or actual rate limits.

## Fixed — P4 independently accepted 2026-09-09 UTC

Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655 returnedP4 PASS,
confirming this bug's acceptance criteria on555verifiedsourcefiles. Independent
fullPython1320pass10skip, readonlyCLI/treeidentity andactualGit tests pass;
cycle1query/consumer/reuseevidence retainedbyhash. [Review report](../../../logs/structured-component-assembly/20260909-publication-repair/review-report.md).
Offline implementation acceptance only; liveadoption separate.
