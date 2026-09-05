# Architecture Surface Coverage Plan

## Status and objective

Implementation and the architecture-only audit are complete and locally
validated as of 2026-09-05. Rollout remains intentionally paused. The
corrected offline canary passed review. Live-agent comparison was cancelled by
user direction, so phase 5 uses deterministic source-fixture replays and a
separate source review of two pinned, comparison-only files under
`architecture/`. The resulting selection remains provisional; pipeline workers
and global enforcement remain disabled pending a separate rollout decision.

The read-only rollout audit of the existing `architecture/` tree completed on
2026-09-05. It measured the warning surface and recurring evidence gaps without
launching agents, reading pipeline logs or source checkouts, modifying generated
documents, or treating legacy files without a coverage sidecar as behaviorally
incomplete. The durable report provides the prioritized extractor/validator
follow-up list required before any enforcement decision.

Make architecture generation account for important behavioral surfaces, not
merely produce valid, evidence-backed additions within broad gap categories.
Retain the analyzer-first partial route, bounded source inspection, explicit
unknowns, and protected final assembly. This extends the
[static migration plan](architecture-context-static-migration.md); it does not
replace its routing or rollout policies.

## Evidence motivating this work

The rhods-operator comparison used repository commit
`4ada791819c522a4cda54f9029ab3e4056ed31ed`:

- Codex run: `logs/pipeline/20260905T032122Z/generate-architecture/rhods-operator.run.json`.
- Generated documents: `architecture/rhoai-3.6-ea.2/rhods-operator.md` and
  `architecture/rhoai-3.6-ea.2.claude/rhods-operator.md`.
- Codex preserved 274 analyzer rows and successfully added three rows. All six
  observed source files were justified, and validation reported no warnings.
- Conditional metrics authentication appeared in the source output for
  `cmd/main.go:480-515`, but was not incorporated into the document.
- The analyzer context identified a Namespace watch at
  `internal/controller/services/auth/auth_controller.go:63`, but did not convey
  the named-namespace predicates establishing the MaaS/Kuadrant relationship.
  The agent did not inspect that controller.
- The routed categories were authentication, integration points, internal
  dependencies, and FIPS compliance. The agent focused on gateway authentication
  and used exactly the suggested six unique files.
- Reported input peaked at 101,996 tokens against a reported 258,400-token
  context window; no compaction event was observed. Context exhaustion is not
  established. Attention dilution and model variability remain hypotheses.

These observations identify two distinct failure modes: available evidence
omitted during synthesis, and missing behavioral evidence not investigated.
Neither prior document is ground truth: the Claude version also made overly
strong FIPS/linkage claims. Expected findings must be checked against source.
Historical logs and generated outputs are local evidence, not durable fixtures
or authorized synthesis inputs.

## Scope and boundaries

- Cover component generation first; expose coverage summaries for downstream
  platform architecture and diagram consumers without treating unresolved
  relationships as established facts.
- Use the same semantic contract for Claude and Codex. Tool adapters may differ,
  but a missing telemetry observation must not be confused with missing source
  evidence or a confirmed absence.
- Do not hand-edit generated architecture, weaken merge protections, or infer
  completeness from a successful run, fact count, or readiness label.
- Do not initially increase pipeline context limits, globally raise file budgets,
  or enable subagents inside component generation. Evaluate those changes only
  after measuring coverage. Implementation-time delegation below is separate.
- Keep this independent of the pending JSON patch migration. Coverage evidence
  may reference accepted changes through either supported patch format.

## Implementation execution: Sol-led, multi-model

When executing this plan, use `gpt-5.6-sol` as the lead implementer and
orchestrator, and delegate suitable bounded work to `gpt-5.6-luna`. This is the
requested development workflow, not a change to the generation pipeline's
model selection or partial-route no-subagent policy.

### Responsibilities

- **Sol owns design and integration:** read the complete plan and repository
  instructions, establish the coverage contract, choose phase-sized work units,
  coordinate assignments, review patches, and verify the integrated result.
  Retain decisions about applicability, semantic completeness, analyzer identity,
  conditional behavior, and merge/promotion guarantees with Sol.
- **Luna implements bounded assignments:** fixture construction from specified
  source evidence, schema-validation cases, report-field wiring, and mechanical
  changes with agreed interfaces and explicit expected behavior. Start with a
  metrics-authentication regression assignment and review it before expanding
  delegation. Do not assign Luna the whole plan or responsibility for declaring
  architectural completeness.
- **An independent reviewer checks substantive changes:** use a fresh Sol review
  session or a human reviewer, separate from the authoring context. Review the
  source evidence, diff, and acceptance criteria directly, not just worker
  summaries. Another model session is an additional check, not proof of correctness.

### Execution protocol

1. Sol reads the full plan, inspects the current worktree, and moves the pending
   implementation task to current when implementation actually starts. Establish
   source-verified expected behaviors before asking workers to implement them.
2. For each phase, issue explicit worker briefs containing the model ID, objective,
   allowed files, interfaces, source fixtures, expected positive and negative
   behavior, verification commands, and stop/escalation conditions. Share only
   the relevant context, plus the invariants workers must preserve.
3. Parallelize independent work with disjoint file ownership. Serialize edits to
   shared schema, orchestration, and skill files; workers must not overwrite
   another worker's or the user's changes. Sol owns integration and shared ledger
   updates. Workers return changed paths, tests actually run, results, and open
   questions; they do not independently mark the overall task complete.
4. Sol inspects every returned diff and runs integrated checks. Escalate ambiguous
   semantics, unexpected failures, or scope expansion back to Sol rather than
   allowing workers to weaken assertions, invent applicability, or silently
   broaden their assignments.
5. Require independent review after the coverage-contract/validator work and
   after behavioral analyzer changes, before advancing to live canaries. Include
   omission, false-positive, unsupported-claim, and merge-loss cases. Passing
   tests written by the same worker are necessary but not sufficient evidence.
6. Execute and verify one phase at a time, recording results and remaining work.
   Keep live generation experiments opt-in and rollout decisions separate. Do
   not launch the whole pipeline merely to test a local schema or extraction rule.

Use the available harness's explicit model-selection mechanism and verify the
selected model in worker metadata where available. If mixed-model delegation is
unavailable, disclose that limitation rather than labeling same-model workers
as Luna; request direction before substituting a different execution strategy.
Do not build new delegation infrastructure solely to satisfy this plan without
separate approval.

This allocation is an execution preference, not a claim of demonstrated model
reliability on this task. Sol itself produced the omissions motivating the plan.
Judge all implementations against source-verified regressions and independent
review, not a model's completion summary.

## Proposed coverage contract

A category such as authentication contains multiple surfaces. Seed applicable
surfaces from analyzer facts, source-linked candidates, and component-role
checklists. Examples for an operator include:

- Metrics authentication and authorization.
- Admission behavior and serving identity.
- Gateway login modes and callback boundaries.
- Controller RBAC propagation and named-resource watches.
- Outbound credentials and API dependencies.
- Initialization ordering and configuration/TLS-profile lifecycle.
- Build crypto signals versus verified runtime compliance.

Use reusable role-based rules, not rhods-operator names or a universal checklist
that assumes every component is an operator. Uncertain applicability remains
visible; lack of extraction is not evidence that a surface is absent. A bounded
read may identify additional surfaces, which must be added to the inventory.

Propose a versioned component-local coverage sidecar with records containing:

- Stable surface ID, parent category, component role, and applicability basis.
- A concrete question, priority, and source-linked candidate locations.
- Disposition: `documented`, `unresolved`, or `not-applicable`.
- Source/analyzer evidence and final section or fact identity for documented
  behavior; reason and remaining question for unresolved behavior.
- Evidence supporting a not-applicable decision; agent assertion alone is
  insufficient.

Separate observed reads, agent dispositions, and validator findings. A cited
file or existing heading does not prove that the document expresses the
behavior. An unresolved entry satisfies accounting, not completeness. Report
documented and unresolved counts separately so writing unknown everywhere
cannot produce a misleading perfect coverage score.

## Implementation sequence

### 1. Establish source-verified regression fixtures

- Capture minimal, sanitized source snippets and expected behaviors for
  conditional metrics authentication and named namespace watches.
- Include gateway OAuth/OIDC/external-auth modes and FIPS uncertainty so added
  breadth does not lose existing strengths or reward unsupported certainty.
- Record the source revision and compare like-for-like analyzer/skill versions.
  Do not require gitignored historical logs for automated tests.
- Add a small representative corpus spanning operators, services, and
  manifest-centric components, including valid not-applicable cases.

Exit: reproducible tests distinguish evidence unavailable, evidence available
but omitted, explicit unresolved behavior, and unsupported claims.

### 2. Add surface-level planning and synthesis review

- Have the orchestrator provide a bounded initial surface inventory alongside
  routed categories, with priorities and evidence locations.
- Update the summary skill to plan across applicable surfaces before spending
  the source-read budget. Closing one gateway question must not close all of
  authentication or internal dependencies.
- Require a final evidence-to-output review: map findings already encountered
  to the candidate document and account for every required surface.
- Preserve the soft budget: allow justified targeted follow-ups for remaining
  questions; record unresolved surfaces when evidence cannot be obtained.
- Express allowed inspection operations in harness-neutral terms and map them
  to each adapter, avoiding contradictory Claude-only tool instructions.

Exit: the metrics fixture is documented without additional source reads, and
an uninspected named-watch surface is investigated or explicitly unresolved.

### 3. Validate coverage against the promoted document

- Validate sidecar schema, required IDs, dispositions, evidence references,
  duplicates, and missing records.
- Reconcile document references after merge and assembly. A rejected candidate
  addition cannot count as documented in the final output.
- Use narrow deterministic assertions for structured behavior where possible.
  Narrative semantic completeness still requires fixture-based evaluation or
  review; do not label a structural check a semantic guarantee.
- Add actionable warnings distinguishing extraction gaps, inspection gaps,
  synthesis omissions, merge losses, and unverifiable coverage claims.
- Start warning-only. Report structural validity, coverage accounting, and
  unresolved safety-critical surfaces separately. Define blocking policy only
  after a reviewed canary establishes acceptable false-positive rates.

Exit: a structurally valid document can still receive a coverage warning, and
the warning identifies the missing surface rather than a generic category.

### 4. Improve analyzer behavioral evidence

- Extract supported controller watch predicates, including literal named
  namespaces, with controller identity and source ranges.
- Extract conditional metrics enforcement, preserving the configuration branch,
  authentication/authorization filter, and associated serving surface.
- Preserve package-qualified identities so similarly named controller handlers
  do not collapse unrelated relationships.
- Emit explicit unresolved evidence for unsupported wrappers or dynamic values;
  do not generalize from a method name alone.
- Project these behaviors into the compact context, rendered baseline, and
  gap evidence index. Prioritize uncovered surfaces over repeated generic hints.

Exit: both initial omissions become deterministic facts or precise unresolved
questions, with positive and negative extraction fixtures.

### 5. Evaluate budgets and optional subsection workers

Execution note: the requested live comparison was superseded by the
user-directed no-live-agent constraint. The durable canary therefore separates
two repeated deterministic fixture replays per condition from two single
architecture-file observations. The latter have complementary 0.50 recall and
cannot measure repeat variability, latency, cost, tokens/cache, source reads,
discovery calls, analyzer preservation, or merge outcomes. This supports only a
provisional choice; it does not justify workers or broader enforcement.

Run a staged, repeated comparison using pinned source, analyzer, skill, model,
and harness settings. Change one factor at a time:

1. Current baseline versus surface planning/review.
2. Add behavioral analyzer extraction.
3. Compare existing versus surface-aware soft budget allocation.
4. Only if coverage remains inadequate, trial bounded subsection workers.

Measure source-verified surface recall, unsupported claims, unresolved counts,
analyzer preservation, merge rejection, unique files/read ranges, discovery
calls, latency, token usage, and cache usage. Keep cumulative token usage
separate from per-request context size. Repeated runs are needed to distinguish
systematic improvements from model variability.

If workers are tested, give each explicit surfaces and a small evidence bundle;
share read accounting and a total budget. Return intermediate findings to one
assembler, not concurrent edits to the final document. This requires a deliberate
change to the partial route's current no-subagent policy and a recorded decision.

Exit: choose the least complex variant that reliably improves verified coverage
without increasing unsupported claims or violating preservation guarantees.
Record cost/latency tradeoffs before any broader rollout.

### 6. Audit warning quality across the existing architecture tree

Status: complete on 2026-09-05. The audit found 901 canonical component
documents and 149 valid document/analyzer pairs representing 80 repository
identities. All 149 analyzers predate `behavioral_evidence` and all 149 lack a
coverage sidecar, so the corpus cannot measure behavioral recall, false-positive
rate, or disposition/read/merge outcomes. It can measure nomination breadth:
526 surface occurrences include 314 required and 212 high-priority
nominations. Runtime FIPS is nominated for every eligible artifact even though
138 artifacts across 72 repository identities report zero FIPS facts. Keep
enforcement warning-only; refresh stored analyzer evidence and narrow FIPS
applicability before evaluating warning quality.

Generation cohorts are intentionally separate. The project-owned
`arch-analyzer` was introduced in the 3.6 era. The 654 pre-3.6 component
documents used an external `architecture-analyzer`, while the LLM retained full
control of the generated summary; they are not missing project-analyzer
artifacts and are not comparable coverage baselines. Another 98 documents in
3.6-era or rolling directories have no stored project-analyzer artifact and
remain unclassified by this on-disk audit.

Run a deterministic, read-only audit over component documents and analyzer
artifacts already stored below `architecture/`:

1. Discover canonical component document/analyzer pairs and record excluded or
   malformed entries without changing them.
2. Build the same role-based surface inventory used by generation and aggregate
   nominated surfaces by platform, component role, priority, and evidence
   capability.
3. Keep legacy sidecar absence separate from coverage findings. A missing
   sidecar means disposition/read/merge telemetry is unavailable; it does not
   prove that the document omits a behavior.
4. Report exact behavioral evidence already present in analyzer JSON, precise
   unresolved behavioral questions, recurring generic candidates, and analyzer
   versions that cannot yet emit the new evidence.
5. Select a deterministic representative review set spanning operators,
   services, and manifest-centric components. Rank follow-up work by repeated
   required surfaces and safety impact, while preserving explicit unknowns.
6. Write JSON and Markdown reports with input fingerprints and tests for stable
   ordering, role stratification, malformed inputs, duplicate platform copies,
   and the missing-sidecar distinction.

The audit consumes on-disk architecture data only. Historical documents remain
comparison inputs and never become synthesis evidence. It must not infer false
positive rates or semantic recall from structural matches alone.

Exit: a reproducible report quantifies audit eligibility, legacy telemetry
availability, nominated required surfaces, analyzer evidence capability, and a
small prioritized follow-up list. Coverage remains warning-only and workers
remain disabled.

## Remaining work: checkpoint and rollout preparation

The completed implementation and audit tasks remain done. The following work
is pending, not evidence that rollout has been approved. Continue the Sol-led
implementation/review protocol for code changes. This plan update authorizes
neither commits nor live model runs, artifact regeneration, or policy changes.

### 0. Isolate and checkpoint the completed work

Before further changes, inventory the broadly dirty worktree and distinguish
surface implementation, tests, documentation, and evaluations from pre-existing
user edits and untracked generated architecture. Record exact paths and a
recoverable checkpoint; obtain approval for the intended commit scope before
staging or committing. Do not bulk-add generated outputs, discard unrelated
changes, or assume every modified file belongs to this effort.

### 1. Fix FIPS applicability

An empty `category_coverage.fips_compliance` record must not by itself nominate
a universally required runtime-FIPS surface. Require an explicit applicability
basis from concrete build, packaging, crypto, runtime evidence, or an explicit
policy requirement. Zero facts must not silently become not-applicable: retain
uncertain applicability when the evidence does not settle it. Build flags or
provider presence must not become proof of runtime compliance.

Add positive, empty-category, ambiguous, and explicit-negative regressions;
independently review the change. Rerun the reproducible audit and report the
nomination delta, without claiming that fewer nominations demonstrate better
semantic recall. Close the FIPS bug only after its acceptance tests pass.

### 2. Restore the repository-wide validation baseline

Investigate the reported 12 pytest collection errors caused by absent legacy
benchmark trees and the two Ruff findings in
`tests/test_component_output_naming.py`. Restore required inputs or explicitly
retire obsolete test dependencies with documented rationale; do not blanket-skip
tests or weaken assertions to obtain green results. Keep baseline repair separate
from surface feature changes and rerun full pytest/Ruff plus preservation tests.

The last handoff reported 65 latest focused tests, 137 earlier phase tests, and
132 preservation tests with 3 skips, plus passing Go tests/lint and report
reproduction. These are separate checkpoints, not additive totals or a claim
that repository-wide validation is already clean.

### 3. Refresh eligible analyzer artifacts and repeat the audit

When source inputs and scoped regeneration approval are available, rebuild the
project analyzer and refresh selected 3.6-era/rolling artifacts at pinned source
revisions. Record analyzer revision, source identity, configuration, and output
fingerprints; preserve historical comparison inputs and use isolated outputs
where possible. Record unavailable source inputs instead of silently changing
revisions or fetching a different release.

Begin with rhods-operator, then a representative operator/service/manifest set.
Confirm behavioral evidence is emitted and rerun the audit. Keep the 654
pre-3.6 external-analyzer documents separate, and leave the 98 unclassified
documents unclassified until actual provenance supports reassignment. Refreshing
analyzer JSON alone does not create agent coverage sidecars or establish
generated-document quality.

### 4. Run the deferred repeated live canary

Model access returning is necessary but not authorization: obtain explicit
approval to lift the no-live-agent constraint, including models, repetition
count, and run/cost limits. Use identical pinned source and refreshed analyzer
inputs for Claude and Codex/Sol, separate output directories, and no historical
summary as synthesis input. Start with rhods-operator before expanding the set.

Check promoted documents for conditional metrics enforcement, MaaS/Kuadrant
watch behavior, OAuth/OIDC/external-auth distinctions, and accurate FIPS
limitations. Measure repeated-run recall, unsupported claims, unresolved surfaces,
warning quality, preservation, merge outcomes, source reads, latency, and token
usage. Compare with historical observations without presenting them as a matched
live baseline. Require independent review of the canary report. Retain the
offline report's provisional status until new evidence supports an update.

### 5. Make separate enforcement and worker decisions

Use the refreshed audit and reviewed live canary to decide whether any scoped
enforcement change is justified. Define thresholds, false-positive tolerance,
fallback/rollback, and affected components before approval. Decide independently
whether remaining gaps justify a bounded worker experiment; approval for
enforcement does not authorize workers or vice versa. Warning-only enforcement
and disabled component workers remain the defaults unless explicitly changed.

### 6. Continue JSON Patch contract work

Continue the existing pending JSON Patch task as the next merge-hardening
implementation after this evidence-quality checkpoint. Do not make patch work
implicitly contingent on approving rollout; a decision to retain warning-only
coverage is a valid outcome. If live evaluation remains unavailable, record the
deferment and request reprioritization rather than enabling policies by default.

## Acceptance criteria

- Conditional metrics authentication and MaaS/Kuadrant watch semantics are
  represented correctly in the source-verified rhods-operator evaluation.
- OAuth/OIDC distinctions and FIPS limitations remain accurate.
- Every seeded required surface is accounted for; unresolved is distinguishable
  from documented and not-applicable is evidence-backed.
- Missing applicable surfaces and facts lost during merge produce actionable
  diagnostics even when architecture structure validation succeeds.
- Tests run without live agents. Under the later user-directed no-live-agent
  constraint, both harnesses are represented only by SHA-256-pinned on-disk
  architecture files and the comparison explicitly records its measurement
  limits.
- Existing table ownership, provenance, source-read justification, and promotion
  tests remain passing. Prior architecture documents are never synthesis inputs.
- The completed offline canary records its measurement limits. Preservation,
  cost, latency, and repeat reliability require the separately authorized live
  follow-up; they are not established by deterministic fixture replay.
- Global enforcement and worker adoption require separate rollout decisions.

## Tracking

- [Implementation task](../tasks/done/improve-architecture-surface-coverage.md).
- [Resolved coverage bug](../bugs/fixed/architecture-synthesis-omits-behavioral-surfaces.md).
- [Read-only rollout audit](../tasks/done/audit-architecture-surface-rollout.md).
- [Open FIPS applicability bug](../bugs/open/surface-inventory-nominates-empty-fips-category.md).
- [Checkpoint and validation baseline](../tasks/current/checkpoint-surface-work-and-restore-validation.md).
- [Fix FIPS applicability](../tasks/pending/fix-surface-fips-applicability.md).
- [Refresh analyzer evidence and audit](../tasks/pending/refresh-surface-analyzer-evidence.md).
- [Deferred repeated live canary](../tasks/pending/run-surface-coverage-live-canary.md).
- [Separate rollout decisions](../tasks/pending/decide-surface-coverage-rollout.md).
- [JSON Patch contract](../tasks/pending/replace-markdown-change-record-with-json-patch.md).

Likely implementation areas are the summary skill and references,
`lib/phases/architecture.py`, routing/context construction, `src/arch-analyzer`,
both harness telemetry adapters, and the generation/evaluation tests. Confirm
exact modules for follow-ups; this documentation update makes no runtime changes.
