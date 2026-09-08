# ADR-0023: Keep Surface Coverage Warning-Only and Subsection Workers Disabled

## Status

Accepted

## Date

2026-09-05

## Context

Surface-level planning, post-merge validation, and behavioral analyzer
extraction are implemented. The deterministic fixture replay reaches complete
recall without unsupported claims at the behavioral-extraction condition, but
that replay is a contract test rather than a model run.

The two pinned on-disk `rhods-operator` summaries each cover two of four
source-reviewed surfaces. The Claude summary also contains three source-refuted
FIPS, package, or linkage claims. Neither stored run supplies repeated-run,
latency, cost, token, source-read, preservation, or merge telemetry.

The architecture-tree audit finds 149 valid project-analyzer/document pairs,
but all 149 analyzers lack `behavioral_evidence` and all 149 components lack a
coverage sidecar. The audit therefore cannot estimate behavioral recall or a
warning false-positive rate. The nine-artifact refresh preflight pins exact
source commits, but the source checkouts, exact analyzer revision, and analyzer
configuration are unavailable under the current architecture-only constraint.

## Decision

Make two separate no-rollout decisions:

1. Keep surface-coverage validation warning-only for every component. No
   coverage warning may block final document promotion.
2. Keep component-generation subsection workers disabled. Do not run a worker
   experiment from the deterministic replay alone. This decision does not
   change ordinary pipeline concurrency across independent components.

No component enters a new enforcement or worker scope. Existing analyzer-first
partial routing, merge protection, and fallback behavior continue unchanged.

Any future enforcement proposal must provide a refreshed, independently
reviewed cohort and repeated controlled canary evidence that meets all of these
entry gates:

- 100% structurally valid sidecars and accounting for every seeded required
  surface, including explicit unresolved and evidence-backed not-applicable
  dispositions;
- zero unsupported claims on required or high-priority surfaces across every
  reviewed repetition;
- at least 0.90 source-verified required-surface recall in every repetition;
- zero analyzer-row preservation failures and zero accepted facts lost during
  merge or final assembly; and
- no more than 5% false-positive coverage warnings overall, with zero
  false-positive warnings on required surfaces, across the complete reviewed
  cohort.

Before enabling blocking behavior, the proposal must also identify the exact
components, include an operator-controlled switch back to warning-only, and
demonstrate that rollback. Before a subsection-worker trial, the non-worker
surface-aware condition must still miss the recall gate, and the trial must
define shared read/token limits, one final assembler, an opt-in component list,
and a default-off rollback.

## Consequences

- Current generation behavior does not change.
- The provisional behavioral-extraction selection remains useful for local
  deterministic testing but does not authorize broader rollout.
- The completed analyzer refresh and repeated live canary remain separate
  evidence tasks; restored model access did not authorize either rollout
  decision.
- Future evidence can supersede this decision without weakening current merge
  or promotion safeguards.
- The repeated live `rhods-operator` canary did not meet these entry gates:
  Claude missed required surfaces, Codex repetition 1 made an unsupported
  initialization-ordering claim, three sidecars were structurally invalid,
  every final assembly lost two analyzer-rendered RBAC rows, one candidate
  surface was also lost, and the reviewed warning false-positive rate was
  27.3%. The canary is rejected and the no-rollout decision remains in force.

## Related Records

- [Architecture surface coverage plan](../plans/architecture-surface-coverage.md)
- [Rollout decision task](../tasks/done/decide-surface-coverage-rollout.md)
- [Analyzer refresh input manifest](../../evaluations/architecture-surface-coverage/refresh-input-plan.md)
- [Offline canary report](../../evaluations/architecture-surface-coverage/report.md)
- [Architecture-tree audit](../../evaluations/architecture-surface-coverage/rollout-audit.md)
- [Repeated live canary](../../evaluations/architecture-surface-coverage/live-canary/report.md)
