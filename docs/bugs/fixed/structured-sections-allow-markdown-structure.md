# Bug: Structured Sections Allow Markdown Structure

Status: fixed. Found by independent Fable phase-one review, 2026-09-06.

Structured section text accepts fences and other structural Markdown, allowing later headings to be swallowed.

Requirements: SC-07. Source: `src/arch-analyzer/internal/structured/validate.go`.
Evidence: `logs/structured-component-assembly/20260906-kickoff/p1-review-report.md`
and retained review stdout/probes. Repair and independent re-review required.

Independently accepted by Fable cycle 3, 2026-09-06. Evidence:
`logs/structured-component-assembly/20260906-kickoff/p1-review3-report.md`.
