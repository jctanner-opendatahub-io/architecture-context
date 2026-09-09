# Final reuse comparison incorrectly treats available source checkouts as missing

Status: fixed — independently accepted in completed P5 review cycle 2.

The provisional final-evidence driver `reproduce_reuse_comparison` only recomputes
saved totals and reports that source checkouts/raw paired outputs are unavailable.
The source-checkout claim is false: the workspace `checkouts` symlink points to
`/data/checkouts`; all184 paths for the saved92pairs exist with matching HEAD/tree.
182 are clean, and two models-perf-benchmark-data checkouts have local deletions.

Fresh extraction/comparison from a recorded committed analyzer build is required
by P5 and can be performed offline. Preserve existing checkouts; isolated clean
copies of the two dirty commits and committed e0f6f367 analyzer sources/binary
have been prepared. Complete the actual fresh comparison, preserve failed/interim
claims, and correct final reports/matrix. Candidate matching remains distinct
from verified reuse; no missing telemetry may be backfilled.

Evidence and prepared input paths:
`logs/structured-component-assembly/20260909-final-evidence/coordinator-source-correction.md`,
`coordinator-reuse-source-audit.json`, `coordinator-prepared-inputs.json`.
No source extraction or live model call was made by the coordinator. Gate remains
unaccepted until fresh evidence and independent review cover this correction.

## Independent closure — 2026-09-09

Fable/high reviewer `b72d66cb-5ba6-4411-9dcb-7b7ec437700b` explicitly verified the acceptance
criteria in section 6 of `logs/structured-component-assembly/20260909-ordering-review/review-report.md`.
Final report SHA-256: `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
The completed verdict is PASS; the earlier rate-limited draft alone
was not accepted. Historical failure evidence is preserved. Separate
rare-input ordering and materialization-error robustness follow-ups
remain open. Live evaluation and default adoption remain on HOLD.
