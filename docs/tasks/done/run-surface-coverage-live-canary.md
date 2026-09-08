# Task: Run Repeated Surface Coverage Live Canary

Status: done. On 2026-09-05 the operator
approved two sequential
`rhods-operator` repetitions per exact model, a 30-minute wall-clock limit per
run, and a Claude cap of $20 per run/$40 aggregate. The Codex arm is limited to
two single-turn runs with recorded token usage because its harness exposes no
dollar-cap control.

Follow step 4 of the [plan](../../plans/architecture-surface-coverage.md) after
the refreshed analyzer audit. Compare Claude and Codex/Sol against identical
pinned inputs in isolated outputs; begin with rhods-operator, then a reviewed
representative set. Historical documents are comparison-only.

Acceptance: independently reviewed report of repeated behavioral recall,
unsupported claims, warnings, uncertainty, preservation, merge results, reads,
latency, and token usage. Preserve provisional conclusions where measurement
remains unavailable. This task does not authorize enforcement or workers.

Use exactly `claude-opus-4-6` for the Claude arm and `gpt-5.6-sol` for the Codex
arm. Do not use aliases, configured defaults, fallback models, or substitute
revisions. The operator confirmed Claude availability through first-party
authentication. The live launch must explicitly remove
`CLAUDE_CODE_USE_VERTEX`, `ANTHROPIC_VERTEX_PROJECT_ID`, and `CLOUD_ML_REGION`
from the process environment and abort unless the resulting Claude provider is
first-party. The commented Vertex settings in `.env` must remain commented.

The smallest qualifying proposal is two sequential repetitions per model for
`rhods-operator` only, with a 30-minute wall-clock limit per repetition. The
Claude proposal applies a $20 maximum per repetition and $40 aggregate maximum;
the Codex harness exposes token telemetry but no dollar-cap control, so its hard
bounds are two single-turn runs and 30 minutes per run. Stop on the first model,
input-integrity, provider, budget, or promotion failure. Do not expand the
cohort without a separately reviewed result and authorization.

The operator accepted these bounds. Stop on the first model, input-integrity,
provider, budget, or promotion failure and record the result before continuing.

## Recorded result

All four isolated run records identify the exact requested models, pinned
source and refreshed analyzer inputs, and a clean source checkout. The
operator-run Claude preflight recorded first-party `claude.ai` authentication,
and every launch removed the Vertex selectors. The retained artifacts do not
include a hashed per-run provider-preflight transcript. Aggregate Claude cost
was $3.768565 against the $40 cap; Codex reported 2,410,593 cumulative tokens
across two single-turn runs.

The corrected reproducible
[live-canary report](../../../evaluations/architecture-surface-coverage/live-canary/report.md)
scores promoted output against source. Codex covered all four required surfaces
in both repetitions, but repetition 1 made an unsupported
initialization-ordering claim outside those surfaces; Codex therefore passed
the full source-review gate only once. Claude scored 0.50 required-surface
recall in both repetitions. Repetition 1 has six unsupported claims after the
first independent review found a missed gateway-proxy flow claim.

That review also found a promotion failure in every run. Each preseed and
candidate contains the analyzer-rendered `opendatahub-operator-metrics-reader`
and `metrics-reader` RBAC rows, while all four promoted documents omit them.
Merge reports still record 274 unchanged rows and zero restorations. Claude
repetition 2 additionally lost a candidate FIPS section. Three coverage
sidecars were structurally invalid, and 12 of 44 warnings were confirmed false
positives.

The four agent processes completed and copied inputs remained hash-identical,
but the canary is rejected because analyzer output was not preserved. No tracked
generated architecture changed. Coverage remains warning-only and subsection
workers remain disabled.

Independent review first rejected the report because it missed the two
unsupported claims and analyzer-row losses described above. A fresh re-review
then found one stale controller-runtime version in the corrected source basis.
After changing that reference to the pinned `v0.24.1` and making the evaluator
reject dependency-qualified references that differ from the retained analyzer
input, final independent review accepted the report with no blocking or
material findings. The task is complete because the authorized measurement and
review are complete; the measured canary remains rejected.
