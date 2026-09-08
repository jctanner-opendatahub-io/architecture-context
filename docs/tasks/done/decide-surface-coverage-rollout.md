# Task: Decide Surface Coverage Rollout

Status: done. The separate decisions are to make no rollout change: coverage
remains warning-only and component-generation subsection workers remain
disabled.

Follow step 5 of the [plan](../../plans/architecture-surface-coverage.md).
Record separate decisions for scoped enforcement and optional generation-worker
experiments, with acceptance thresholds, false-positive tolerance, scope, and
rollback. Keeping current defaults is a valid decision.

Acceptance: explicit operator-approved decisions supported by measured evidence;
no implicit enablement from implementation completion, restored model access,
or a green offline canary. Warning-only coverage and disabled workers remain
unchanged until separately authorized. The JSON Patch follow-up is complete;
its merge-hardening result does not supply the missing rollout evidence.

## Decision record

[ADR-0023](../../decisions/ADR-0023-keep-surface-coverage-warning-only.md)
records independent enforcement and worker decisions, the empty rollout scope,
the evidence gaps, thresholds for reconsideration, and required rollback
controls. At decision time, the on-disk audit could not measure warning false
positives because all 149 eligible analyzers predated behavioral evidence and
all 149 lacked coverage sidecars. The two pinned summaries each have 0.50
reviewed surface recall. The later nine-artifact analyzer refresh established
new structured behavioral evidence. The repeated live `rhods-operator` canary
subsequently measured generated summary recall and warning quality: Codex passed
the full source-review gate in one of two repetitions, Claude passed neither,
three of four sidecars were structurally invalid, every promotion lost two
analyzer-rendered RBAC rows, one candidate surface was also lost during
assembly, and 12 of 44 warnings were false positives. Those measurements
reaffirm the existing no-rollout decision; they do not support a scoped
enforcement or worker change.
