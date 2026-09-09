# Bug: Reuse ignores the recorded model mismatch

Status: open.

F-P3-4: A prior response reporting a different model is marked reuse-ineligible in its envelope but still reused by the private loader. Enforce producer eligibility, preserve actual identity, and handle primary versus auxiliary model usage explicitly.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review1-report.md and p3-review1-evidence/.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
