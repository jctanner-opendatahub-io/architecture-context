# Task: Improve Architecture Surface Coverage

## Status

Done 2026-09-05. Implementation, local verification, and independent phase 5
review passed.

## Goal

Distinguish supported additions from adequate behavioral coverage, and prevent
known evidence from disappearing during architecture synthesis.

## Plan

Follow [Architecture Surface Coverage](../../plans/architecture-surface-coverage.md):
source-verified fixtures, surface planning and final review, warning-only
post-merge coverage validation, behavioral analyzer improvements, then measured
budget and optional worker experiments.

Implementation uses the plan's Sol-led multi-model protocol: Sol owns design and
integration, Luna receives bounded assignments, and substantive changes receive
independent review. This does not enable workers in the generation pipeline.

## Acceptance

The rhods-operator regression captures conditional metrics authentication and
named namespace-watch integrations without losing gateway/FIPS accuracy.
Required surfaces are explicitly accounted for, unsupported claims are not
rewarded, and existing ownership/promotion guarantees remain intact. Complete
the plan's automated tests and reviewed canary before broader enforcement.

## Progress

- Source-verified the pinned `rhods-operator` behaviors at revision
  `4ada791819c522a4cda54f9029ab3e4056ed31ed`: conditional secure-metrics
  authentication/authorization, literal MaaS and Kuadrant namespace watches,
  distinct gateway authentication modes, and the explicit non-FIPS CSV signal.
- Started phase 1 fixture construction with the required bounded Luna assignment.
- Completed the locally testable phase 1-3 checkpoint: source-sanitized
  regression fixtures, deterministic surface inventory and sidecar validation,
  planning/final-review skill contracts, promoted-document coverage diagnostics,
  and orchestration/report wiring. Focused verification passed with 62 tests;
  the related preservation suite passed with 130 tests and 3 skips.
- Paused before behavioral analyzer extraction for the required independent Sol
  review of the coverage contract and validator checkpoint.
- Addressed the first independent review's seven findings: harness-only read
  observations, exact table-cell identities, strict evidence and applicability
  validation, immutable seeded fields, inventory-conservative invalid-sidecar
  recovery, manager-specific metrics nomination plus glob observation, and a
  Codex immutable-input integrity check. Corrected focused tests pass (90), as
  does the related preservation suite (131 with 3 skipped); awaiting re-review.
- Addressed the second review's three remaining blockers: range-aware telemetry
  reconciliation, planning-only source candidates, and conservative recovery
  for every top-level structural violation. The third-review checkpoint passes
  92 focused tests and 131 preservation tests with 3 skips.
- Corrected the third review's Codex adapter finding: unparsed successful read
  actions now retain bare unknown bounds and cannot acquire read-through-EOF
  credit. The adapter-to-validator regression keeps distant bounded evidence
  unresolved. The fourth-review checkpoint passes 93 focused tests and 132
  preservation tests with 3 skips.
- Completed the local phase 4 behavioral-analyzer checkpoint. The analyzer now
  emits typed conditional metrics-enforcement and named-watch-predicate facts,
  including exact source ranges, package-qualified controller identities,
  literal namespace names and resolved event targets. Dynamic values,
  unsupported wrappers, mismatched branches, and same-named imports fail closed
  as explicit unresolved records. These facts reach the compact context,
  rendered baseline, gap index, and surface inventory; compact projection is
  bounded and unresolved behavior precedes generic gap hints. The pinned
  `rhods-operator` checkout produces the expected `cmd/main.go:485-500` metrics
  fact and both auth controller Namespace-watch facts. Full analyzer tests,
  106 focused Python tests, 132 preservation tests with 3 skips, Ruff, schema
  validation, and diff checks pass. Phase 5 remains paused for the required
  independent review.
- Addressed the phase 4 review findings with adversarial regressions. Observed
  metrics behavior now requires an exact controller-runtime manager `Metrics`
  binding, a single lexical metrics-options object, a stable configuration
  expression, and no intervening reassignment. Named-watch proof now trusts only
  exact current-module helpers and direct handler composition. All precise
  behavioral gaps survive the generic category cap in analyzer JSON, while the
  compact renderer reports omitted candidates. Observed schema proof fields are
  nonempty and observed watch records require an event target. Pinned extraction
  retains all 18 precise unresolved watch gaps while preserving the three
  expected observed facts. Full analyzer tests, 114 focused Python tests, 132
  preservation tests with 3 skips, Ruff, schema validation, pinned output
  assertions, and diff checks pass. Phase 5 remains gated on re-review.
- Tightened the corrected phase 4 proof through its final state: rebinding the
  returned metrics options or overwriting `FilterProvider`/`SecureServing`
  after the guarded assignment now yields unresolved evidence, while unrelated
  certificate field writes remain supported. A watch containing any additional
  nested `ToNamed` or handler wrapper also remains unresolved. The review's
  exact overwrite and mixed-target probes now pass.
- Closed the final re-review control-flow case by requiring exactly one return
  from the metrics IIFE, of the same lexical options object and after the filter
  assignment. Nested alternate returns before or inside the secure branch now
  remain unresolved; returns inside separate nested function literals do not
  affect the outer IIFE proof.
- Completed the offline phase 5 canary after live-agent execution was cancelled
  by user direction. The durable evaluation pins the source, analyzer, schema,
  skill, model labels, and both comparison-only architecture-file SHA-256s. Two
  deterministic fixture replays per condition change one factor at a time and
  select behavioral extraction as the earliest passing condition. Separate
  source review gives each single on-disk output 0.50 surface recall on
  complementary surface pairs; Claude has three unsupported FIPS/package/linkage
  claims, while Codex has none. The selection remains provisional because the
  files cannot establish repeat variability, latency, cost, token/cache use,
  read activity, analyzer preservation, or merge outcomes. Workers remain off
  and validation remains warning-only. Phase-focused tests pass (137), the
  preservation suite passes (132 with 3 skips), full arch-analyzer Go tests pass,
  and focused Ruff and report reproducibility checks pass. Awaiting independent
  canary review before task completion or bug closure.
- Addressed the independent canary review's consistency findings. Deterministic
  run provenance must match the manifest's controlled harness and model;
  workers and coverage enforcement are validated as disabled and warning-only,
  and the recommendation reports those validated settings. Unsupported
  observations require source-refuted claims attributed to every unsupported
  surface. Recommendation condition, recall, and complementarity language is
  derived from validated results. Direct mutation regressions and report
  regeneration pass. Independent corrected phase 5 review passed.
- The linked Agentic Work Ledger specification is absent from this checkout;
  root `AGENTS.md` rules and established task/session-log conventions govern.
