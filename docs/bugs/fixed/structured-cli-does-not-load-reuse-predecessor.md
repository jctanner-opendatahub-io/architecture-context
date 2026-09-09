# Bug: Structured CLI does not load an explicit reuse predecessor

Status: open, P3 integration gap reported by implementer.

The programmatic API can accept AcceptedSnapshot/ReuseTarget but the opt-in CLI
always records predecessor-not-supplied. This leaves the required reuse-first
pipeline integration incomplete. P3 must load an explicitly selected, validated
prior private staged result, build current trusted target inputs/Go normalization,
and preserve normal bounded misses. P4 will integrate published four-file input
locations and retain essential metadata in those core files.

Evidence: logs/structured-component-assembly/20260907-resume/p3-implementation-report.md.

## Fixed — P4 independently accepted 2026-09-09 UTC

Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655 returnedP4 PASS,
confirming this bug's acceptance criteria on555verifiedsourcefiles. Independent
fullPython1320pass10skip, readonlyCLI/treeidentity andactualGit tests pass;
cycle1query/consumer/reuseevidence retainedbyhash. [Review report](../../../logs/structured-component-assembly/20260909-publication-repair/review-report.md).
Offline implementation acceptance only; liveadoption separate.
