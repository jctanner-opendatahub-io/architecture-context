# Bug: Surface Coverage Document References Produce False Positives

Status: open.

The repeated `rhods-operator` live canary emitted 44 surface-coverage warning
messages. Source review confirmed 12 false positives: the validator reported a
missing document reference or synthesis omission even though the promoted
document contained the relevant source-supported behavior. Both Codex
repetitions were affected, including required metrics, gateway, named-watch,
and FIPS surfaces.

Evidence is retained in
[`live-canary/report.md`](../../../evaluations/architecture-surface-coverage/live-canary/report.md)
and the per-run coverage artifacts below `live-canary/runs/`. The warning review
separates these messages from sidecar-contract defects and useful semantic
signals.

Expected behavior: section, fact-identity, and table references should match
source-supported promoted content without requiring verbatim model phrasing.
Repairs must remain conservative: a broader matcher must not turn partial or
unsupported content into documented coverage. Coverage remains warning-only
until a source-reviewed cohort meets ADR-0023's false-positive gates.
