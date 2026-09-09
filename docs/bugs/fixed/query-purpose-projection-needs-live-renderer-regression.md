# Query purpose projection needs a current-renderer regression guard

Status: open. Found by independent SC-18 review cycle 1 on 2026-09-07.

Severity/scope: Medium; SC-04/SC-18.

F2: query Purpose/PurposeFull compatibility derives prose using twelve semantically copied renderer helpers. Static fixture parity cannot detect a producer-side prose change in the default test suite. Add a durable default test against the current single renderer or a producer-owned projection in P4; no second renderer.

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
