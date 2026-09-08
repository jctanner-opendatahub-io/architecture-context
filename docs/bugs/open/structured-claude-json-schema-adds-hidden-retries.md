# Bug: Claude JSON schema option adds unrecorded internal tool retries

Status: open.

F-P3-6: output_format maps to CLI --json-schema, implemented via StructuredOutput tool with CLI retry logic. This contradicts the parent-owned one-response budget and can put output in structured_output rather than retained result text. Remove implicit provider-side response-repair orchestration or prove/record/bound it; parent validation already exists.

Evidence: logs/structured-component-assembly/20260907-resume/p3-review2-report.md and p3-review2-evidence/.
