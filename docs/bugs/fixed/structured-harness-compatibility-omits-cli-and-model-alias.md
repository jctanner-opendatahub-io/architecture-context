# Bug: Reuse compatibility omits CLI and resolved model alias identity

Status: open.

P3 cycle2 N9/N14: Claude CLI composes context but only SDK version is keyed; requested alias opus enters key instead of actual table-resolved model identity. Changes to either may reuse a snapshot under changed model-visible context. Add audited actual CLI build/version and resolved model identity before reuse decision; no provider invocation needed.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review2-report.md and p3-review2-evidence/.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
