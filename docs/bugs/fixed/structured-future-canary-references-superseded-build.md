# Future canary instructions conflate analyzer builds

Status: fixed — independently accepted in completed P5 review cycle 2.
Found: 2026-09-09 in final independent review cycle 1.

The future live-canary note calls the modified product analyzer (binary
98fa820c…) the P5 reference and points to the rejected interim comparison.
The actual fresh comparison uses committed e0f6f367, binary 458c04cb…,
archive 5f753cdb…. Both builds exist and have separate roles: canary replay
versus fresh source comparison. Neither authorizes future live execution.

Acceptance: document both roles with verified identities and accepted evidence
references, preserve superseded evidence, require freezing the actual future
run build, retain execution/cost/stop/rollback bounds, and independently review.
If the ordering repair produces another build, identify that separately too.

## Independent closure — 2026-09-09

Fable/high reviewer `b72d66cb-5ba6-4411-9dcb-7b7ec437700b` explicitly verified the acceptance
criteria in section 6 of `logs/structured-component-assembly/20260909-ordering-review/review-report.md`.
Final report SHA-256: `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
The completed verdict is PASS; the earlier rate-limited draft alone
was not accepted. Historical failure evidence is preserved. Separate
rare-input ordering and materialization-error robustness follow-ups
remain open. Live evaluation and default adoption remain on HOLD.
