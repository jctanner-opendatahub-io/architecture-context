# Bug: Structured Repo Lineage Bypasses Validation

Status: fixed. Found by independent Fable phase-one review, 2026-09-06.

Rendering-view validation copies repo_lineage from the reviewed document without source fact accounting or a bound component-map input.

Requirements: SC-08/SC-09. Source: `src/arch-analyzer/internal/structured/validate.go`.
Evidence: `logs/structured-component-assembly/20260906-kickoff/p1-review-report.md`
and retained review stdout/probes. Repair and independent re-review required.

Independently accepted by Fable cycle 3, 2026-09-06. Evidence:
`logs/structured-component-assembly/20260906-kickoff/p1-review3-report.md`.
