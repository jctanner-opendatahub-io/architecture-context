# Fresh reuse comparison forced an inappropriate distribution

Status: fixed — independently verified in P5 review cycle 1.
Found: 2026-09-09 during the final offline comparison.

The first fresh extraction driver supplied `--distribution rhoai.next` instead
of preserving the committed analyzer's empty default selector. Consequently,
104 of 184 extractions failed; 80 succeeded. Independent review classified 98
as wrong-selector failures and six as the separate padded Git-size parse bug.
These failures do not establish missing source objects or reproduce the two
historical extraction failures.

The complete failed attempt is retained under
`logs/structured-component-assembly/20260909-fresh-reuse/fresh-evidence/`.
The direct Sol/high worker removed the forced selector and added a regression
assertion before a separate corrected attempt. No product code or source
checkout changes are required.

Acceptance: independently verify the corrected command, retained first attempt,
fresh raw outputs and failure accounting, and meaningful regression coverage.
P5 review cycle 1 verified the corrected commands in attempts 2 and 3 and an
independent 184-side rerun, with the focused regression passing. Reviewer
Fable/high session `4d779de7-348b-4720-8325-55d82e5183bc` explicitly marked
these criteria met. The overall P5 gate remains unaccepted for separate
ordering and documentation findings.
