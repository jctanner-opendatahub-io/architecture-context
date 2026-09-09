# Bug: Codex default selection sends a placeholder model name

Status: open.

F-P3-7: missing --model sends configured-default literally as params.model rather than None. CLI promises configured Codex default. Resolve actual default before input binding, retain resolved identity/settings, and avoid substituting an unavailable placeholder model.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review2-report.md and p3-review2-evidence/.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
