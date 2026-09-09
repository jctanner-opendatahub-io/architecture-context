# Bug: Preflight failure detail bypasses credential redaction

Status: open, F-P3-10; non-blocking review finding to repair with F-P3-9.
Found independently 2026-09-08.

The adapter's preflight wrapper constructs `RateLimitError` from the original
SDK exception text. The new private diagnostic writes that text to `detail`,
while its sibling `provider_error.message` is redacted. A synthetic Bearer token
therefore survives in `preflight-diagnostic.json`. The producing-call path uses
an already-redacted result and passed this check. No actual credential exposure
was observed; reproduction used a fake token with model transports blocked.

Evidence: [additional review §4](../../../logs/structured-component-assembly/20260908-rpc-quota-repair/review-report.md),
`review-evidence/test_seam_probes.py/.out` and `seam-probe-results.jsonl`.

Acceptance: preflight error detail uses the existing credential-redaction rule;
a regression checks the entire persisted diagnostic for absence of the synthetic
secret, while quota classification and useful structured codes remain intact.
No unrelated redaction redesign or public schema change is needed.

## Fixed — independently accepted 2026-09-08

Fable/high session `a6ccbff3-0617-487d-9223-2549189ce1f4` returned P3 PASS,
including this finding. [Review evidence](../../../logs/structured-component-assembly/20260908-quota-shapes/review-report.md).
Full Python1274 pass/10skip, focused283 pass, independent boundary probes27 pass;
all547 reviewed source hashes verified unchanged. Offline tests only.
