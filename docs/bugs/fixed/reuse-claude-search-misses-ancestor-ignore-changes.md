# Bug: Claude search reuse misses ancestor ignore changes

Status: fixed. Found in independent P2 review cycle 2, 2026-09-07.

F10 medium SC14: parent .gitignore changes search result without scoped tree identity change; Claude search record stays complete and hits. Record/verify context, replay safely, or conservatively miss unavailable search contexts.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review2-report.md`
and `p2-review2-probes/`. Repairs require fresh independent acceptance.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
