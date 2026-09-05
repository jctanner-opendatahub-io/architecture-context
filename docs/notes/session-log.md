# Session Log

- 2026-09-05: Received approval for the recorded architecture-surface commit
  scope. Staged exactly 25 tracked modifications plus 50 untracked source,
  test, documentation, and evaluation files; excluded unknown `TEST.sh`, both
  generated architecture trees, and ignored checkpoint artifacts. Index and
  whitespace checks passed. Pre-commit verification passed with 248 preservation
  tests and four skips, 96 focused feature tests, all Go module tests, Go lint,
  scoped Ruff, and byte-identical canary/audit report regeneration. A broader
  pytest attempt reconfirmed all 12 absent-benchmark collection modules: three
  initially excluded and nine additional failures. That baseline repair remains
  scheduled after the FIPS applicability fix.

- 2026-09-05: Started the plan's worktree checkpoint gate before the FIPS
  applicability fix. At base HEAD `28728163dde09c1007e0c2cb6d9e794cd3c06539`,
  classified 25 tracked modifications as 18 surface-only plus seven mixed
  surface/Codex/ledger paths. Classified 2,028 untracked paths as 48 surface
  files, two Codex telemetry ledger records, unknown `TEST.sh`, and 1,977
  generated architecture files. Created ignored binary patches, path manifests,
  grouped archives, a two-document pinned comparison archive, and checksums
  below `tmp/checkpoints/architecture-surface-coverage-20260905/`. Proposed one
  integrated 25-tracked-plus-50-untracked commit while excluding the unknown
  script, generated trees, and checkpoint artifacts. Nothing was staged or
  committed; awaiting the plan-required scope approval.

- 2026-09-05: Updated the surface coverage plan to separate completed implementation/offline audit from paused rollout. Added pending follow-ups for worktree checkpointing, FIPS applicability, repository validation repair, scoped analyzer refresh, authorized repeated live canaries, and separate enforcement/worker decisions. Preserved legacy-cohort and missing-sidecar distinctions; no code, generated outputs, commits, or live runs changed.

- 2026-09-05: Corrected the rollout audit's generation-history interpretation
  from project-owner guidance. The project `arch-analyzer` begins in the 3.6
  era; 654 pre-3.6 documents used an external `architecture-analyzer` with the
  LLM retaining full control of summary generation. The report now treats them
  as an incomparable legacy cohort instead of implying absent analyzer output.
  Of the remaining documents, 149 have valid project-analyzer pairs and 98 in
  3.6-era or rolling directories lack a stored project analyzer and remain
  unclassified. Updated durable reports, tests, plan, task, and evaluation
  guidance without modifying generated architecture.

- 2026-09-05: Completed the architecture-only surface rollout audit. Added a
  deterministic read-only scanner, fixture tests, and byte-reproducible JSON and
  Markdown reports. The scan found 901 canonical component documents, 149 valid
  document/analyzer pairs, 80 repository identities, and 526 nominated surface
  occurrences (314 required, 212 high priority). Every eligible analyzer lacks
  the new `behavioral_evidence` field and every eligible component lacks a
  coverage sidecar, so the report makes no behavioral recall, false-positive,
  disposition, read, or merge claims. Runtime FIPS was nominated for every
  eligible artifact while 138 artifacts across 72 repositories report zero
  FIPS facts; filed an open applicability bug and ranked evidence refresh first.
  The 65 focused tests, focused Ruff, byte reproduction, and diff check passed.
  Coverage remains warning-only, workers remain disabled, and generated
  architecture was not modified.

- 2026-09-05: Started the architecture-surface rollout audit requested after
  completion of the coverage plan. Extended the plan with a read-only phase 6
  that consumes only component documents and analyzer artifacts below
  `architecture/`, keeps legacy sidecar absence separate from behavioral
  coverage, aggregates role/surface/evidence capability, and produces a
  reproducible representative audit before enforcement. Opened the audit task
  in `docs/tasks/current/`. Initial discovery found 149 analyzer artifacts and
  no surface-coverage sidecars; no agent, log, source-checkout, or generated
  architecture mutation is authorized for this audit.

- 2026-09-05: Independent corrected phase 5 review passed, completing the
  architecture-surface-coverage plan. Promoted the implementation task to done
  and the behavioral-surface omission bug to fixed. The reviewed durable canary
  retains its provisional behavioral-extraction selection: user direction
  cancelled live agents, so the comparison uses two single SHA-256-pinned
  architecture files plus separate deterministic fixture replays and cannot
  establish model variability, latency, cost, token/cache use, source-read
  activity, analyzer preservation, or merge outcomes. Pipeline subsection
  workers remain disabled and coverage enforcement remains warning-only; either
  change requires a separate rollout decision.

- 2026-09-05: Corrected the phase 5 canary after independent review. The
  evaluator now rejects deterministic mode/harness/model provenance drift,
  enabled workers, and non-warning coverage enforcement; recommendation safety
  fields come from those validated settings. Unsupported statuses require
  source-refuted claims attributed to each unsupported surface, and the
  recommendation derives its selected condition, recall, and complementarity
  language from validated results. The regenerated report is byte-reproducible.
  Canary tests passed (23), the focused phase suite passed (137), full
  arch-analyzer tests and the repository Go lint target passed, focused Ruff
  passed, and the diff check was clean. Submitted for re-review without
  promoting the current task or open bug.

- 2026-09-05: Completed the local phase 5 architecture-surface canary under the
  user-directed no-live-agent constraint. Added a durable evaluator, manifest,
  deterministic replay, source-review protocol, JSON/Markdown report, and
  regressions. The manifest pins source/analyzer/schema/skill identities plus
  the Claude and Codex architecture-file SHA-256s; the evaluator derives recall
  from statuses and restricts each review basis to that surface's pinned source
  references. Two deterministic replays per one-factor condition provisionally
  select behavioral extraction. The separate on-disk comparison scores both
  single outputs at 0.50 recall on complementary surface pairs and records three
  unsupported Claude FIPS/package/linkage claims. Runtime/repeat telemetry is
  explicitly unavailable, workers remain off, and validation remains
  warning-only. Phase-focused tests passed (137), preservation tests passed (132
  with 3 skipped), full arch-analyzer Go tests passed, and focused Ruff and
  report-reproducibility checks passed. Submitted for independent canary review
  before moving the task or bug to done/fixed. The repository-wide Python test
  command remains blocked during collection by 12 tests that import the absent
  legacy `benchmark/analyzer-assisted-v1` and `benchmark/consumer-v1` trees; the
  repository-wide Ruff command separately reports the pre-existing import order
  and unused `Path` in `tests/test_component_output_naming.py`. Neither legacy
  issue was changed as part of this work.

- 2026-09-05: Tightened phase 4 metrics control-flow proof after final-state re-review. The metrics IIFE must contain exactly one return, return the same lexical options object, and place that return after the filter assignment. Nested early alternate returns before or within the secure branch now force an unresolved record; nested function literals remain separate scopes. Direct adversarial tests, full analyzer tests, 114 focused Python tests, 132 preservation tests with 3 skips, Ruff, pinned extraction/render assertions, and diff checks passed. Phase 5 remains paused for re-review.

- 2026-09-05: Closed two remaining phase 4 fail-open paths found by re-review. Metrics proof now follows the lexical options object through its matching return and rejects later rebinding or writes to `FilterProvider`/`SecureServing`, while retaining supported post-filter certificate writes. Named-watch proof counts handler and `ToNamed` calls across every watch argument, so a supported target plus any nested foreign target remains unresolved. Direct reset/rebind/SecureServing/certificate and extra-target regressions passed; the review probe now contains only the stable metrics record as observed and marks the reset and mixed watch unresolved. Full analyzer tests, 114 focused Python tests, 132 preservation tests with 3 skips, Ruff, schema validation, pinned extraction/render assertions, and diff checks passed. Phase 5 remains paused for re-review.

- 2026-09-05: Corrected phase 4 after independent review. Conditional metrics facts now attach only to exact `ctrl.NewManager`/`ctrl.Options.Metrics` syntax and require a direct returned metrics-options object, stable identical branch expression, lexical object identity, and no intervening reassignment; dead, foreign, dynamic-call, shadowing, and reassignment regressions fail closed. Named-watch extraction now requires exact current-module predicate/reconciler/handler imports and direct `WithEventHandler(ToNamed(...))` composition; matching foreign suffixes, arbitrary wrappers, and mixed handlers remain unresolved. Precise behavioral gaps are no longer lost to the 12-item generic cap or path-only deduplication, and compact output reports candidates retained only in JSON. Schema rules reject empty observed proof fields and require observed watch targets. The pinned `rhods-operator` extraction preserves the three expected observed facts and all 18 precise unresolved watch gaps. Full analyzer tests, 114 focused Python tests, 132 preservation tests with 3 skips, Ruff, schema validation, pinned output assertions, and diff checks passed. Phase 5 remains paused for re-review.

- 2026-09-05: Completed the phase 4 behavioral-analyzer checkpoint for architecture surface coverage. Added typed, source-ranged extraction for conditional controller-runtime metrics authentication/authorization and literal named-resource watch predicates with package-qualified controller identities and resolved event targets. Unsupported imports/wrappers, dynamic values, and mismatched conditions remain explicit unresolved evidence. Projected the records into bounded compact context, rendered baseline, gap evidence, and surface inventory. The pinned `rhods-operator` checkout at `4ada791819c522a4cda54f9029ab3e4056ed31ed` emitted `cmd/main.go:485-500` with `oconfig.MetricsSecure` and `filters.WithAuthenticationAndAuthorization`, plus the MaaS and Kuadrant Namespace watch records at auth-controller lines 63-76. Full arch-analyzer Go tests passed; focused Python tests passed (106); preservation tests passed (132 with 3 skipped); Ruff, JSON Schema validation, JSON parsing, and diff checks passed. Paused before phase 5 for the required independent Sol review.

- 2026-09-05: Corrected Codex read telemetry after the third coverage-contract review: only directly parsed bounded reads receive line bounds, while unrecognized successful reads now emit bare unknown bounds instead of being treated as line 1 through EOF. An adapter-to-validator regression confirms `head -20 cmd/main.go` cannot verify or suppress inspection for `cmd/main.go:480-500`, while preserving file and operation counts. Focused tests passed (93), preservation tests passed (132 with 3 skipped), Ruff passed, and the diff check was clean. Submitted for a fourth review before analyzer extraction.

- 2026-09-05: Tightened the architecture-surface-coverage checkpoint after re-review. Source-read evidence now requires a telemetry interval that fully covers the cited lines; candidate inspection requires overlap; open-ended reads retain a known start and bare unknown ranges confer no credit. Source candidates remain planning inputs and cannot prove documentation. Any top-level sidecar contract mutation now restores seeded unresolved and safety accounting. Focused tests passed (92), preservation tests passed (131 with 3 skipped), Ruff passed, and the diff check was clean. Submitted for a third independent review before analyzer extraction.

- 2026-09-05: Corrected all seven first-checkpoint independent review findings before analyzer work. Coverage observations now come only from real harness telemetry and explicitly represent unavailable observation; table references include expected cell identity; evidence, not-applicable claims, paths, analyzer pointers, top-level roles, and immutable seeded fields are validated; missing or invalid sidecars conservatively retain seeded unresolved and safety accounting; metrics nomination isolates operator-manager evidence and glob candidates reconcile with telemetry; and Codex restores and fails on planning-input mutation while retaining declared sidecar output. Focused tests passed (90), preservation tests passed (131 with 3 skipped), Ruff passed, and the diff check was clean. Submitted for re-review with phase 4 still paused.

- 2026-09-05: Completed the first architecture-surface-coverage checkpoint: source-sanitized role and rhods-operator regression corpus, deterministic surface inventory and coverage sidecar, planning/final evidence review instructions, promoted-document diagnostics, and warning-only telemetry integration. Reviewed and corrected the bounded Luna metrics fixture, including a valid disposition plus separate unsupported-claim status. Focused tests passed (62), related preservation tests passed (130 with 3 skipped), and focused Ruff plus diff checks passed. Paused before analyzer extraction for independent Sol review.

- 2026-09-05: Started architecture surface coverage implementation. Source-verified the pinned rhods-operator metrics-authentication condition, literal MaaS/Kuadrant namespace watches, gateway authentication modes, and explicit non-FIPS CSV signal; moved the task to current and began the required bounded Luna fixture assignment. The linked Agentic Work Ledger specification is absent, so repository task and session-log conventions are being followed directly.

- 2026-09-05: Added explicit Sol-led, Luna-assisted implementation orchestration to the surface coverage plan, with bounded assignments, disjoint file ownership, phase verification, independent review checkpoints, and a disclosed fallback when mixed-model execution is unavailable. Clarified that development delegation does not enable generation-pipeline subagents.

- 2026-09-05: Added the architecture surface coverage plan, pending implementation task, and observed-omission bug. The plan stages source-verified regression fixtures, surface-level synthesis review, post-merge coverage diagnostics, analyzer behavioral extraction, and later budget/worker experiments. No runtime or generated architecture changes.

- 2026-09-04: Fixed Codex SDK enum serialization and checkout-relative source-read telemetry; kept reporting failures terminal with original telemetry retained. Verified 43 focused tests and completed-log replay (six observed files, no read-justification warnings). Generated outputs and historical reports were left unchanged.

- 2026-09-04: Reviewed the `praxis-proxy` checkouts for RHOAI 3.6 EA.2. Added `grid` to `rhoai-3.6-ea.2.include_components` because it is a deployable Kubernetes operator with CRDs and Helm artifacts planned for 3.6 GA, despite not yet appearing in the EA catalog.
- 2026-09-04: Added per-`extra_repos` `name_prefix` support so Praxis repositories use descriptive checkout/component aliases while preserving canonical GitHub repository identities.
- 2026-09-04: Fixed targeted pipeline discovery to resolve per-organization checkout directories from platform configuration instead of passing the checkout root into provenance analysis.
- 2026-09-04: Propagated prefixed repository aliases through component-map keys, included-repository checkout resolution, static-analysis/analyzer paths, architecture generation metadata and documents, platform aggregation, and diagrams; added migration cleanup for prior raw-name artifacts.
- 2026-09-04: Fixed Rust analyzer extraction for Cargo members using `version.workspace = true`, discovered while analyzing `praxis-policy`; added a workspace-inheritance regression test.
- 2026-09-05: Fixed analyzer rendering to resolve canonical Git repository identities back to prefixed component-map keys, and made final architecture promotion enforce the component key from the output filename.
- 2026-09-04: Added a selectable Claude/Codex agent harness, using the existing Codex login and shared checked-in skills; completed and tested the fetch plus component-discovery vertical slice.
- 2026-09-04: Changed the Codex harness to consume the public turn notification stream, flush JSONL events during execution, show live event names, preserve terminal result telemetry, and propagate cancellation with useful diagnostics.
- 2026-09-04: Replaced raw Codex event-name output with readable streamed agent messages and concise command start/completion notices; retained full command output and protocol events only in JSONL logs.
- 2026-09-04: Regenerated the pre-sync RHOAI 3.6 EA.2 component discovery map from nine checkout roots, retaining canonical Praxis repository names under prefixed component keys; validation passed with 17 discovered components and 82 exclusions.
- 2026-09-04: Added temporary Codex discovery workspaces, explicit worker instructions, staged shared skills, and parent validation/atomic promotion after the discovery trace showed pipeline exploration and reuse of the prior Claude map. Verified valid, invalid, absent, and failed candidates with mocked agent execution; live output verification remains with the operator.
- 2026-09-04: Added the resolved SKILL.md path and supporting directory directly to Codex text input, including how to resolve CLAUDE_SKILL_DIR references, to eliminate unnecessary skill-location searches in generation runs.
