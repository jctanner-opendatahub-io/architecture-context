# Bug: Reuse replay trusts persisted command arguments

Status: fixed. Found in independent P2 review cycle 2, 2026-09-07.

F8 high SC14/25: replay executes unvalidated argv, including --pre programs and outside roots. Must reject before any subprocess launch; validate actual argv and its consistency with recorded scope/options in both replay modes.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review2-report.md`
and `p2-review2-probes/`. Repairs require fresh independent acceptance.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
