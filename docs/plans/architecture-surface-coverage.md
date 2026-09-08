# Architecture Surface Coverage Plan

## Status and objective

Implementation, the architecture-only audit, the analyzer refresh, and the
version index are complete as of 2026-09-05. The approved repeated live canary
ran, but its first independent review found a promotion failure and rejected
the initial report. Independent re-review accepted the corrected report on
2026-09-06; the canary result itself remains rejected.
Rollout remains intentionally paused. The corrected offline canary remains a
deterministic contract fixture and its two on-disk files remain comparison-only.
The separate live canary used refreshed inputs and measured repeated behavior,
cost, token use, reads, preservation, merge outcomes, and warning quality.
Pipeline workers and global enforcement remain disabled under ADR-0023.

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
- Keep this independent of the completed JSON Patch migration. Coverage
  evidence may reference accepted changes through either supported patch
  format.

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

## Follow-up work: checkpoint and rollout preparation

The completed implementation and audit tasks remain done. The remaining live
gate is explicitly blocked; none of this work is evidence that rollout has been
approved. Continue the Sol-led
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

Implementation and independent review completed on 2026-09-05. On the identical
architecture fingerprint, source-linked runtime-FIPS nominations changed from
149 to 97 and 52 evidence-free category records became explicit uncertain
observations without nomination. The four required regression classes, audit
aggregation, fingerprint guard, and byte reproduction pass.

A pre-review edge-case pass subsequently split the 97 nominations into 90
uncertain static-signal questions and seven applicable source-backed limitation
questions. All retain uncertain claim support. It also covers category-level
explicit negatives and common negative wording while refusing to seed an
evidence-free negative category record.

The fresh independent Sol review initially rejected three boundary classes:
unsafe URI/drive sources and suppressed zero-fact negatives, cross-record
provenance borrowing, and generic structured statuses becoming FIPS claims.
After corrections and regressions, the final 64-test boundary matrix and
byte-identical audit reproduction passed. The reviewer accepted the change with
no blocking defects, so the task and bug are closed. The nomination delta remains
planning-rule evidence rather than semantic-recall evidence.

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

Completed on 2026-09-05. Commit `f8a6f6ff` had intentionally removed the two
legacy benchmark trees, so their benchmark-only tests and launchers were
explicitly retired rather than skipped or restored. Active telemetry and
failure-proposal schemas moved to `schemas/`; surviving stale assertions were
updated to current repository contracts. Full pytest now passes 829 tests with
nine skips, full Ruff passes, and the repository test/lint targets pass across
Python, all Go modules, overlays, platforms, and 901 architecture documents.
ADR-0018 records the decision.

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

The architecture-only preflight completed on 2026-09-05. A deterministic
[refresh input manifest](../../evaluations/architecture-surface-coverage/refresh-input-plan.md)
pins nine artifacts (three each for operator, service, and manifest roles), puts
`rhods-operator` first, and hashes every stored analyzer output plus comparison
document. All nine artifacts pin an exact source commit and analyzer version
`0.1.0-dev`, but none contains its source checkout, exact analyzer revision, or
analyzer configuration; all also predate `behavioral_evidence`. Regeneration is
recorded as not run under the current architecture-only constraint. No branch,
tag, release, or other revision was substituted, and generated architecture was
not modified. That record remains the before-state.

The exact local checkouts were subsequently identified and authorized for use.
All nine had the manifest origin, a clean worktree, and the exact pinned HEAD.
The completed isolated refresh pins analyzer base
`39209078846f15f1909373c106d2d665a907a509`, source-diff SHA-256
`6376b9ffdf60420986f5d34b5f55ed145cf55eb85587a9028fe52fefa6a38c84`,
full source-tree SHA-256
`a6a9cb810949c275f7650074fe02b6adefe2495123a24348e70e015ba93bb6a7`,
and binary SHA-256
`d13d83d5229a6a708507a8932353ce10fb281b1af8c4fe125a94d2a8d34106b8`.
All extraction, render, and schema stages completed for nine artifacts and 157
schemas. The refreshed cohort has three source-observed records and 40 precise
unresolved records; its six zero-record artifacts now explicitly encode an
empty behavioral-evidence list. The JSON and Markdown audit artifacts reproduce
byte-for-byte from retained structured outputs, and generated architecture was
not modified.

Independent review accepted the refresh and the empty-evidence encoder fix with
no blocking findings. The reviewer independently verified the nine checkouts,
recomputed provenance, rebuilt a byte-identical analyzer binary, reviewed the
source facts and unresolved records, reproduced both audit files, and passed
focused Python plus full arch-analyzer Go tests. An optional full independent
`rhods-operator` static-analysis rerun was stopped after several quiet minutes,
so the reviewer did not separately regenerate the 130-schema bundle or render
hashes; the retained outputs and their provenance were independently verified.

### 4. Run the deferred repeated live canary

Model access returning is necessary but not authorization: obtain explicit
approval to lift the no-live-agent constraint, including models, repetition
count, and run/cost limits. Use exactly `claude-opus-4-6` and `gpt-5.6-sol`
against identical pinned source and refreshed analyzer inputs, separate output
directories, and no historical summary as synthesis input. Do not use model
aliases, defaults, fallbacks, or substitutions. Start with rhods-operator before
expanding the set.

The Claude arm must use first-party authentication. Explicitly remove
`CLAUDE_CODE_USE_VERTEX`, `ANTHROPIC_VERTEX_PROJECT_ID`, and `CLOUD_ML_REGION`
from the launch environment, leave the commented Vertex settings in `.env`
untouched, and abort if the provider preflight is not first-party.

Check promoted documents for conditional metrics enforcement, MaaS/Kuadrant
watch behavior, OAuth/OIDC/external-auth distinctions, and accurate FIPS
limitations. Measure repeated-run recall, unsupported claims, unresolved surfaces,
warning quality, preservation, merge outcomes, source reads, latency, and token
usage. Compare with historical observations without presenting them as a matched
live baseline. Require independent review of the canary report. Retain the
offline report's provisional status until new evidence supports an update.

On 2026-09-05 the operator approved and the pipeline completed two sequential
`rhods-operator` repetitions per model, 30 minutes per run, Claude capped at
$20 per run/$40 aggregate, and two single-turn Codex runs with recorded usage.
All four run records preserve the pinned input hashes and record a clean source
checkout. The operator-run preflight recorded first-party `claude.ai`
authentication, and each Claude launch removed the Vertex selectors. The
durable set lacks a hashed provider-preflight transcript, so it cannot
independently re-attest the provider after execution. Claude cost $3.768565 in
aggregate; Codex reported 2,410,593 cumulative tokens.

The corrected reproducible source-reviewed report records 1.00 required-surface
recall in both Codex repetitions, but Codex repetition 1 also contains an
unsupported initialization-ordering claim and therefore only repetition 2
passes the zero-unsupported-claim gate. Both Claude repetitions scored 0.50
required-surface recall: metrics and the named watches were stable, gateway
modes were partial, and runtime FIPS was unsupported once and omitted once.
Claude repetition 1 contains six unsupported claims after adding a missed
gateway-proxy flow claim.

All four promoted documents silently lost two analyzer-rendered non-resource
RBAC rows even though the rows were present in each preseed and candidate. The
merge reports continued to claim 274 unchanged rows and zero restorations.
Claude repetition 2 also lost a candidate FIPS section, three coverage sidecars
were structurally invalid, and 12 of 44 warning messages were false positives.
The analyzer-row loss is a promotion failure under the approved stop condition;
the canary is rejected and cannot support enforcement or a worker experiment.
Independent re-review accepted the corrected report on 2026-09-06 after one
additional dependency-provenance correction. The source review now cites the
pinned controller-runtime `v0.24.1`, and the evaluator rejects stale
dependency-qualified review references. The review independently verified all
retained hashes, source findings, measurements, losses, computed gates,
provenance limits, byte reproduction, validation results, clean checkout, and
absence of tracked architecture changes.

#### Promotion repair after the rejected canary

Completed and independently accepted on 2026-09-06. The analyzer now retains
Kubernetes non-resource URLs and renders a dedicated RBAC column. Promotion
uses disjoint resource, non-resource, mixed, and conservative legacy target
identities; verb-aware internal matching prevents collisions while preserving
the v1 three-cell patch contract. Ambiguous v1 operations fail conservatively,
and legacy rows never acquire URL facts that were not present or source-backed.

Merge reconstruction retains opaque rows and final assembly checks every
Markdown table row, including tables with no configured parser. Any lost row
fails promotion with a durable `analyzer_row_lost_during_assembly` diagnostic.
Arch-doc separately validates every configured synthesis subsection's actual
H2 parent. Misplaced content is neither moved nor accepted: it produces a
structured `synthesis_subsection_parent_mismatch` report that propagates through
merge and the durable architecture run report.

The isolated [promotion repair replay](../../evaluations/architecture-surface-coverage/promotion-repair-replay/report.md)
uses the four retained preseed, candidate, and patch sets without modifying the
original evidence. Three candidates promote with 276/276 mapped and 310/310
total analyzer table rows preserved. Claude repetition 2 is rejected with no
promoted output because FIPS Compliance is under Admission Webhooks instead of
Security. The original canary remains rejected; warning-only coverage and
disabled component workers are unchanged.

A fresh exact `gpt-5.6-sol` reviewer drove fixes for unmapped-table checking,
ambiguous RBAC v1 identities, operation reuse, and legacy table schema upgrade,
then accepted the corrected code and replay with no remaining correctness
findings. Repository-wide pytest passed 948 tests with 10 skips; `make test`,
Ruff, all Go tests and lint/vet, overlay/platform validation, and validation of
901 tracked architecture documents passed. No tracked architecture document
changed and no live generation agent ran for the repair.

### 5. Make separate enforcement and worker decisions

Use the refreshed audit and reviewed live canary to decide whether any scoped
enforcement change is justified. Define thresholds, false-positive tolerance,
fallback/rollback, and affected components before approval. Decide independently
whether remaining gaps justify a bounded worker experiment; approval for
enforcement does not authorize workers or vice versa. Warning-only enforcement
and disabled component workers remain the defaults unless explicitly changed.

Decision completed on 2026-09-05. [ADR-0023](../decisions/ADR-0023-keep-surface-coverage-warning-only.md)
records two separate no-rollout decisions. Coverage stays warning-only for all
components, and subsection workers stay disabled. The decision defines
source-reviewed recall, unsupported-claim, false-positive warning,
preservation, merge, scope, and rollback gates for any future proposal. The
current evidence does not meet those gates, so no component or policy changed.

### 6. Continue JSON Patch contract work

Completed on 2026-09-05. New evidence-gated runs emit a versioned
`ARCHITECTURE_PATCH.json`; JSON Schema, route-budget, evidence, duplicate, key,
and exact candidate/analyzer validation run at the merge boundary. Invalid or
unmatched operations prevent final output and promotion. Historical Markdown
remains a replay-only compatibility reader. A durable sanitized `odh-gitops`
fixture applies five representative rows with zero rejection or restoration.
ADR-0019 records the contract. Repository-wide pytest passes 843 tests with
nine skips, and the repository test and lint gates pass.

### 7. Generate a deterministic version index before diagrams

Status: completed 2026-09-05. The non-agent `generate-index` pipeline phase renders
`architecture/<version>/INDEX.md` from existing local artifacts. No LLM calls,
source-checkout inspection, network fetches, or new synthesis are required.
This is a low-cost Markdown navigation interface for current RFE/STRAT consumers,
not a replacement for `arch-query` or another retrieval benchmark.

**Ordering:** in the default full pipeline, run after component architecture and
platform architecture generation, immediately before diagrams. The index links
to available component documents and `PLATFORM.md`; it explains where to look,
while `PLATFORM.md` explains the platform. Diagram generation may use the index
for navigation but must use the linked evidence for substantive claims. Index
generation must not invoke diagrams or any other agent phase.

Expose an independently runnable `generate-index` phase for an existing version
directory. Preserve explicitly selected pipeline phases rather than silently
adding agent work. For targeted component runs, rebuild the version-wide index
from the complete map and available artifacts, not just the selected component.
An index can be generated after discovery with pending-document entries, but
the required full-pipeline refresh uses the final promoted artifacts.

**Inputs and content:**

- Use `component-map.json`, platform configuration, available analyzer metadata,
  and promoted document metadata/headings. Define deterministic precedence and
  safe fallbacks; a missing description stays unavailable instead of triggering
  a model call. Do not read arbitrary source files to fill gaps.
- List canonical component aliases, including prefixes such as `praxis-`, a
  short existing description when available, component type, and relative links
  to documents that actually exist. Clearly distinguish available from pending
  documentation and stale/mismatched metadata where detectable.
- Keep inventory inclusion separate from current platform integration. Preserve
  included-but-not-integrated components such as Praxis. Report integration as
  unknown unless explicit version-scoped evidence establishes it; `extra_repos`
  or inclusion alone does not establish shipped integration.
- Show planned integration only from explicit configuration or active,
  release-applicable human overlays, with attribution. Never turn a future
  relationship into a current edge. Link relevant corrections rather than
  attempting LLM interpretation of free-form overlay prose.
- Add concise topic navigation from existing categories and actual document
  sections (authentication, serving, training, pipelines, lifecycle). Where those
  are insufficient, use a small explicit maintained mapping; do not infer
  capabilities or relationships from repository names. Mark mappings as
  navigation hints, not proof of behavior.
- Link available coverage/limitations artifacts with their status. Missing
  legacy sidecars mean unavailable telemetry, not missing behavior.

**Implementation and validation:**

- Render with stable ordering, proper Markdown escaping and relative-link
  encoding, atomic replacement, and unchanged-input byte stability. Avoid
  volatile timestamps and write only the requested index.
- Treat `INDEX.md` as reserved version metadata: exclude it from component
  enumeration, platform aggregation inputs, audits, lint rules that expect
  component schemas, and component-diagram job discovery. Inventory components
  must never include the index itself.
- Do not create broken document/section links for pending outputs. Missing
  optional artifacts remain explicit; malformed required inputs produce
  actionable errors without replacing a valid existing index.
- Test prefixes, non-integrated repositories, planned/unknown relationships,
  missing documents/analyzers, legacy versions, overlay applicability, escaped
  names, deterministic reruns, targeted/full phase ordering, and index exclusion.
  Prove offline generation makes zero agent invocations.

Acceptance: a useful, reproducible inventory/topic directory generated at
negligible computation cost, without new claims or duplicated platform prose.
The index primarily reduces consumer navigation overhead; it does not by itself
reduce component synthesis cost. Existing rollout pauses and regeneration
constraints remain in force; this planning addition does not authorize a live
run or edits to generated architecture.

Implementation completed without live generation. The standalone and selectable
pipeline paths use only local structured artifacts; the full pipeline places the
phase after platform generation and before diagrams, while targeted runs execute
it once version-wide. Deterministic atomic rendering, relationship precedence,
pending and legacy inputs, overlay applicability, aliases and escaping, metadata
mismatches, reserved-file exclusions, and zero-agent execution have regression
coverage. ADR-0024 records the contract. Repository-wide Python and Go tests,
Ruff, Go lint/vet, lock validation, and repository data linters pass. Tracked
generated architecture remains unchanged.

## Acceptance criteria

- Conditional metrics authentication and MaaS/Kuadrant watch semantics are
  represented correctly in the source-verified rhods-operator evaluation.
- OAuth/OIDC distinctions and FIPS limitations remain accurate.
- Every seeded required surface is accounted for; unresolved is distinguishable
  from documented and not-applicable is evidence-backed.
- Missing applicable surfaces and facts lost during merge produce actionable
  diagnostics even when architecture structure validation succeeds.
- Offline fixture tests run without live agents. The separately authorized live
  canary retains SHA-256-pinned inputs and outputs for both exact-model arms and
  records its provider, budget, telemetry, and cohort limits.
- Existing table ownership, provenance, source-read justification, and promotion
  tests remain passing. Prior architecture documents are never synthesis inputs.
- The completed offline canary records its measurement limits. The repeated
  live follow-up separately measures preservation, cost or token use, latency,
  reads, merge behavior, warning quality, and repeat reliability for the single
  `rhods-operator` cohort.
- Global enforcement and worker adoption require separate rollout decisions.

## Tracking

- [Implementation task](../tasks/done/improve-architecture-surface-coverage.md).
- [Resolved coverage bug](../bugs/fixed/architecture-synthesis-omits-behavioral-surfaces.md).
- [Read-only rollout audit](../tasks/done/audit-architecture-surface-rollout.md).
- [Resolved FIPS applicability bug](../bugs/fixed/surface-inventory-nominates-empty-fips-category.md).
- [Checkpoint and validation baseline](../tasks/done/checkpoint-surface-work-and-restore-validation.md).
- [Completed FIPS applicability review](../tasks/done/fix-surface-fips-applicability.md).
- [Completed analyzer evidence refresh](../tasks/done/refresh-surface-analyzer-evidence.md).
- [Completed repeated live canary](../tasks/done/run-surface-coverage-live-canary.md).
- [Completed promotion repair](../tasks/done/repair-live-canary-promotion-defects.md).
- [Fixed non-resource RBAC promotion](../bugs/fixed/promotion-drops-analyzer-non-resource-rbac-rows.md).
- [Fixed synthesis-section loss reporting](../bugs/fixed/merge-report-omits-candidate-section-loss.md).
- [Completed separate rollout decisions](../tasks/done/decide-surface-coverage-rollout.md).
- [JSON Patch contract](../tasks/done/replace-markdown-change-record-with-json-patch.md).
- [Deterministic version index](../tasks/done/generate-deterministic-version-index.md).
- [Completion audit and remaining external gate](../notes/architecture-surface-coverage-completion-audit.md).

Likely implementation areas are the summary skill and references,
`lib/phases/architecture.py`, routing/context construction, `src/arch-analyzer`,
both harness telemetry adapters, and the generation/evaluation tests. Confirm
exact modules for follow-ups; this documentation update makes no runtime changes.
