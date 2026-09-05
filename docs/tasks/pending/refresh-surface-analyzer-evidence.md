# Task: Refresh Surface Analyzer Evidence

Status: pending source availability and scoped regeneration approval, after
FIPS applicability and validation-baseline work.

Follow step 3 of the [plan](../../plans/architecture-surface-coverage.md).
Rebuild the analyzer, refresh pinned eligible 3.6-era/rolling inputs starting
with rhods-operator, and rerun the audit. Preserve historical artifacts and
record input/output fingerprints and unavailable inputs.

Acceptance: reviewed behavioral facts and reproducible audit for the refreshed
cohort. External-analyzer and unclassified cohorts stay distinct; absent legacy
sidecars remain unavailable telemetry, not omissions. No live agents required.
