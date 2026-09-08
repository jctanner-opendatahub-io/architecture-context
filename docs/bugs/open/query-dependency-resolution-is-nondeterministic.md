# Query dependency resolution is nondeterministic

Status: open. Found by independent SC-18 review cycle 1 on 2026-09-07.

Severity/scope: Pre-existing; outside bounded SC-18 implementation.

F4: independent reviewer reproduced eight distinct deps JSON outputs over twenty baseline runs due to MLflow versus MLflow Operator resolution. Current behavior is within baseline outputs; no SC18 regression. Watches/webhooks/CRDs also have pre-existing ordering nondeterminism. Preserve evidence and scope separately; do not claim new-route regression or expand the consolidation task silently.

Evidence: `logs/structured-component-assembly/20260907-resume/sc18-review-report.md`,
reviewer `a7b596b1-a251-4e25-8e3b-323dd6f7da0d`, Fable 5.1/high.
The bounded SC18 verdict is PASS subject to dependency recheck; this finding is
non-blocking for that slice and remains tracked independently.
