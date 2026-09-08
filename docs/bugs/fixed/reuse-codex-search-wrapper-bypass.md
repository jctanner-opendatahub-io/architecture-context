# Bug: Codex search classification accepts shell wrappers

Status: fixed. Found in independent P2 review cycle 2, 2026-09-07.

F9 medium SC25: completed-output raw bash/sh wrapper with empty actions or equal unknown-action command becomes complete. Reject wrappers regardless of action/output shape; regress end to end.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review2-report.md`
and `p2-review2-probes/`. Repairs require fresh independent acceptance.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
