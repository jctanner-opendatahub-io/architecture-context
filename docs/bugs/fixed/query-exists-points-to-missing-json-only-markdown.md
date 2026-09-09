# Query exists points to missing JSON-only Markdown

Status: open. Found by independent SC-18 review cycle 1 on 2026-09-07.

Severity/scope: Low; SC-18 compatibility.

F5: exists prints Doc: <version>/<component>.md for a valid JSON-only accepted component even when that derivative is absent. In P4 select an existing authoritative/derivative path and add a JSON-only command regression without changing CLI flags.

Evidence: `logs/structured-component-assembly/20260907-resume/sc18-review-report.md`,
reviewer `a7b596b1-a251-4e25-8e3b-323dd6f7da0d`, Fable 5.1/high.
The bounded SC18 verdict is PASS subject to dependency recheck; this finding is
non-blocking for that slice and remains tracked independently.

## Fixed — P4 independently accepted 2026-09-09 UTC

Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655 returnedP4 PASS,
confirming this bug's acceptance criteria on555verifiedsourcefiles. Independent
fullPython1320pass10skip, readonlyCLI/treeidentity andactualGit tests pass;
cycle1query/consumer/reuseevidence retainedbyhash. [Review report](../../../logs/structured-component-assembly/20260909-publication-repair/review-report.md).
Offline implementation acceptance only; liveadoption separate.
