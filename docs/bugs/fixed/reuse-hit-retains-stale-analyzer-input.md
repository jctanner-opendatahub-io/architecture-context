# Bug: Reuse hit retains stale analyzer input identity

Status: fixed. Found in independent P2 review cycle 2, 2026-09-07.

F11 medium SC15: output updates target identity/evidence but retains prior bundle fingerprint and extraction time; truthful target normalized values rejected. Bind actual target analyzer input without weakening validated output projection or rewriting original synthesis.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review2-report.md`
and `p2-review2-probes/`. Repairs require fresh independent acceptance.

Independent acceptance: Fable cycle 3 PASS, session b7b8d76a-e126-4874-be29-36c2433fe4eb. Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`. All prior evidence and limitations retained. P3 producer/publication integration remains separate.
