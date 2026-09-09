# Analyzer ordering causes unnecessary reuse misses

Status: fixed — independently accepted in completed P5 review cycle 2.
Found: 2026-09-09, F-P5-1, independent Fable review cycle 1.
Requirements: SC-11, SC-13; reassess affected P1 rendering guarantees.

The reviewer reran all 184 extractions with the same committed analyzer and
source identities. Thirteen outputs differed only in list order. Legacy fact
matches changed from 31 to 30; current analyzer-only matches changed from 37
to 36. Repeated extraction of kube-rbac-proxy produced two orderings of the
same security evidence. integration_points, entrypoints and gap_evidence_index
also varied. The semantic fingerprint preserves meaningful list order, so this
causes conservative misses and can unnecessarily repeat synthesis.

Evidence: `logs/structured-component-assembly/20260909-fresh-reuse/review-cycle-1/`
contains the report, independent rerun and repeated-source probes. One concrete
cause is iteration over the Go import map in security_evidence.go without stable
output ordering. The existing query dependency ordering bug does not cover this.

Coordinator decision: repair producer ordering within the authorized plan,
rather than defer the unmet zero-call guarantee. Do not sort arbitrary semantic
lists in the reuse key. Identify unordered producer collections, preserve
meaningful ordering and facts, add meaningful repeatability/reuse regressions,
and renew independent review for affected analyzer/rendering guarantees.

Historical committed-build samples remain intact and must disclose observed
30–31 / 36–37 variation. Do not relabel old binary results as fixed output.
Acceptance requires stable affected producer outputs, no facts lost, zero-call
reuse for identical relevant inputs, proportionate complete checks, honest
evidence updates, and independent P5 acceptance.

## Independent closure — 2026-09-09

Fable/high reviewer `b72d66cb-5ba6-4411-9dcb-7b7ec437700b` explicitly verified the acceptance
criteria in section 6 of `logs/structured-component-assembly/20260909-ordering-review/review-report.md`.
Final report SHA-256: `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
The completed verdict is PASS; the earlier rate-limited draft alone
was not accepted. Historical failure evidence is preserved. Separate
rare-input ordering and materialization-error robustness follow-ups
remain open. Live evaluation and default adoption remain on HOLD.
