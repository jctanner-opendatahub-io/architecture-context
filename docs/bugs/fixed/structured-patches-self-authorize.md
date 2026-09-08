# Bug: Structured Patches Self Authorize

Status: fixed. Found by independent Fable phase-one review, 2026-09-06.

Patch proposals declare their own allowed types and acceptance decisions with no trusted parent policy input.

Requirements: SC-06. Source: `src/arch-analyzer/internal/structured/patch.go`.
Evidence: `logs/structured-component-assembly/20260906-kickoff/p1-review-report.md`
and retained review stdout/probes. Repair and independent re-review required.

Independently accepted by Fable cycle 3, 2026-09-06. Evidence:
`logs/structured-component-assembly/20260906-kickoff/p1-review3-report.md`.
