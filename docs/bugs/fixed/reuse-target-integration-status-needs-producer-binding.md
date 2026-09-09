# Bug: Reuse target integration status needs producer binding

Status: fixed — independently verified in P5 review cycle 1.

F14 low: integration_status and corresponding uncertainty are excluded from reuse invariants as platform-only metadata. P3 must derive them from the actual current component map/configuration, never arbitrary caller or model data.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`.

P5 Fable/high reviewer `4d779de7-348b-4720-8325-55d82e5183bc` verified
run_pipeline_seam resolves each component's integration status from the actual
component map, platform configuration and active overlays before constructing
the request. The real-Go pipeline regression changes the map to current and
reuses with one total synthesis call while updating document identity. It
passed independently in the complete 1330-test run. Closure applies to this
criterion only; unrelated P5 ordering and documentation findings remain open.
