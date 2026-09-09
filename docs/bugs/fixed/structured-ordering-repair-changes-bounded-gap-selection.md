# Ordering repair affects bounded gap-evidence selection

Status: fixed — independently accepted in completed P5 review cycle 2.
Found: 2026-09-09 by the direct Sol/high implementer.

The first repaired analyzer produced matching relevant outputs in two complete
184-side runs (32 legacy matches, 38 analyzer-only matches). Comparing content
to the older build exposed changed selection among gap-evidence navigation
candidates on 22 sides: sorting upstream affected which entries survived a
12-candidate limit. Source facts themselves were unchanged.

Evidence: `logs/structured-component-assembly/20260909-ordering-repair/`
retains both independent runs and the validation helper. The implementer is
assessing ordering/selection sequencing. Do not erase these initial results or
attribute subsequent source changes to their build.

Acceptance: independently assess ordering relative to the candidate limit,
preservation of source facts, stable selection under unordered input traversal,
and justified navigation-candidate changes. Avoid restoring unstable selection
merely to match one old sample. Report exact content differences and renew
repeatability checks against the final repair before closing.

## Independent closure — 2026-09-09

Fable/high reviewer `b72d66cb-5ba6-4411-9dcb-7b7ec437700b` explicitly verified the acceptance
criteria in section 6 of `logs/structured-component-assembly/20260909-ordering-review/review-report.md`.
Final report SHA-256: `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
The completed verdict is PASS; the earlier rate-limited draft alone
was not accepted. Historical failure evidence is preserved. Separate
rare-input ordering and materialization-error robustness follow-ups
remain open. Live evaluation and default adoption remain on HOLD.
