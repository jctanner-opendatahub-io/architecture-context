# Fresh reuse driver mishandles Git entries and dotted output names

Status: fixed — independently accepted in completed P5 review cycle 2.
Found: 2026-09-09 in the second fresh comparison attempt.

The source preparation code interpreted Git's padded `-` size as an integer.
Both versions of mlflow, notebooks, and rhaii-cluster-validation failed before
extraction. Separately, suffix replacement on dotted component names caused
`.github` and `.project` output names to collide. The run reported 178 successful
extractions and 89 complete pairs, but unchanged compare.py received only 88
raw files per side. That report is not a complete comparison. Independent
review also established that the collision affected attempt 1 (39 raw files
per side versus 40 internally compared pairs).

Evidence is retained under
`logs/structured-component-assembly/20260909-fresh-reuse/fresh-evidence-attempt-2/`.
The worker is correcting parsing and output identity, adding regressions, and
preparing a third attempt that carries only uniquely identified, hash-verified
successes and freshly runs the ten affected sides.

Acceptance: verify distinct output files for all paired identities, proper
gitlink handling and disclosed submodule limits, safe carry-forward checks,
retained failures, and agreement between per-pair and unchanged compare.py
counts. No source checkout or historical dataset modifications are required.

P5 review cycle 1 verified all behavioral acceptance criteria and 184 unique
outputs. The coordinator keeps this bug open until the adjacent padded-size
regression requested as O-P5-1 is added and checked in the current repair.

## Independent closure — 2026-09-09

Fable/high reviewer `b72d66cb-5ba6-4411-9dcb-7b7ec437700b` explicitly verified the acceptance
criteria in section 6 of `logs/structured-component-assembly/20260909-ordering-review/review-report.md`.
Final report SHA-256: `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
The completed verdict is PASS; the earlier rate-limited draft alone
was not accepted. Historical failure evidence is preserved. Separate
rare-input ordering and materialization-error robustness follow-ups
remain open. Live evaluation and default adoption remain on HOLD.
