# Bug: Structured Empty Tables Fail Roundtrip

Status: fixed. Found by independent Fable re-review cycle 2, 2026-09-06.

Empty typed table rows are omitted by JSON encoding although decoding and schema require the rows array; normalize emits an unreadable accepted document.

Requirements: SC-07. Executed evidence: kickoff `p1-rereview-report.md`
and retained scratch probes under `/tmp/rereview-*`.
Repair and independent re-review required.

Independently accepted by Fable cycle 3, 2026-09-06. Evidence:
`logs/structured-component-assembly/20260906-kickoff/p1-review3-report.md`.
