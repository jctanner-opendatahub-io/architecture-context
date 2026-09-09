# Bug: Structured route cannot generate with Codex or reuse with Claude

Status: open.

P3 review section5: Codex rejects all structured calls because an all-tools-disable control is not established; Claude declares opaque provider internals incomplete and always misses reuse. These are material unaccepted limitations. The plan requires bounded tool use, not necessarily global tool disabling. Evaluate supported controls and distinguish supplied local context from opaque provider implementation; do not silently reduce scope or invent support.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review1-report.md and p3-review1-evidence/.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
