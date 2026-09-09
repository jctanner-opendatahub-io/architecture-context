# Bug: Structured adapter tests can start an authenticated SDK when a boundary moves

Status: open; required regression protection before final P3 review.

Two implementation test runs reached real Codex SDK startup when a production
boundary changed: removing the old refusal, then adding pre-reuse preflight.
Higher-level runner stubs did not prevent lower-level client construction.
The first incident's provider request/billing cannot be determined. The second
was reported during Codex partB; exact retained evidence remains to reconcile.
No actual rate-limit event has been observed from either retained run.

Offline tests need a default guard at actual provider transport startup, in
addition to scenario-specific stubs. A missing stub must fail before process or
network activity, including preflight. Guard actual SDK start/connect boundaries
while still permitting pure local serialization and --version inspection. Do
not broadly disable unrelated localhost tests or claim the guard covers child
processes it does not intercept.

Evidence: p3-review2-report.md section6 and p3-codex-repair-2/stdout.jsonl under
logs/structured-component-assembly/20260907-resume. Original reports immutable;
record corrections and final guard evidence separately.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
