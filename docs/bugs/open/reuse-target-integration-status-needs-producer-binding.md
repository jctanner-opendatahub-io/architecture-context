# Bug: Reuse target integration status needs producer binding

Status: open, non-blocking P2 follow-up.

F14 low: integration_status and corresponding uncertainty are excluded from reuse invariants as platform-only metadata. P3 must derive them from the actual current component map/configuration, never arbitrary caller or model data.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`.
