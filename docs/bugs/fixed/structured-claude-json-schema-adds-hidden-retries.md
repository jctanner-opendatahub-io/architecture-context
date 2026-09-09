# Bug: Claude JSON schema option adds unrecorded internal tool retries

Status: open.

F-P3-6: output_format maps to CLI --json-schema, implemented via StructuredOutput tool with CLI retry logic. This contradicts the parent-owned one-response budget and can put output in structured_output rather than retained result text. Remove implicit provider-side response-repair orchestration or prove/record/bound it; parent validation already exists.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review2-report.md and p3-review2-evidence/.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
