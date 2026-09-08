# Bug: Codex Discovery Telemetry Does Not Classify rg Searches

Status: open.

Both Codex live-canary runs used targeted `rg` discovery before bounded source
reads, but `rhods-operator.run.json` reports zero
`targeted_discovery_calls`. The retained run telemetry can measure successful
source-read operations and unique files, but it cannot currently distinguish
the observed search calls from other command executions.

Evidence and the measurement limitation are recorded in
[`live-canary/report.md`](../../../evaluations/architecture-surface-coverage/live-canary/report.md).

Expected behavior: the Codex adapter should classify successful bounded `rg`
or equivalent discovery commands consistently with Claude telemetry, without
misclassifying validation, artifact reads, or arbitrary shell commands.
