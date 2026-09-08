# Task: Repair Live-Canary Promotion Defects

Status: done and independently accepted 2026-09-06. Investigation and
regression design started on 2026-09-06.

## Progress

- Read the repository handbook, top-level plan, surface-coverage plan, both bug
  reports, and the four retained canary artifact sets. Confirmed the original
  evidence remains unchanged.
- Verified delegated model selection at launch: a `gpt-5.6-sol` design lead and
  two bounded `gpt-5.6-luna` regression-test assignments. The section suite
  reproduced four expected failures (three controls passed); the RBAC suite
  reproduced nine expected failures (two evidence controls passed).
- Root causes confirmed: the analyzer model discarded Kubernetes
  `nonResourceURLs`; the Python merge excluded empty-resource legacy rows and
  reconstructed tables only from representable rows; arch-doc searched
  configured H3 synthesis subsections only under their allowed parent and had
  no durable failure-report path.
- Repair design accepted: keep the v1 three-cell RBAC patch identity while
  using disjoint resource, non-resource, and conservative legacy target kinds;
  preserve all analyzer table rows through a generic raw-row backstop; validate
  every configured synthesis subsection's actual parent before assembly and
  propagate structured diagnostics through merge and run reports.
- Implemented analyzer URL extraction/rendering, compatibility-safe Python
  identities, opaque-row retention, post-assembly row preservation, structured
  arch-doc reports, and durable runner propagation. Focused regression and
  related merge/phase suites pass.
- Replayed all four immutable candidates offline under
  `evaluations/architecture-surface-coverage/promotion-repair-replay/`: three
  repaired promotions preserve all 276 mapped analyzer rows and all 310 total
  analyzer table rows; Claude repetition 2 is explicitly rejected with
  `synthesis_subsection_parent_mismatch`, no promoted output, and a retained
  merge report. Original evidence hashes match before and after replay, and the
  original canary remains rejected.
- A fresh `gpt-5.6-sol` reviewer found three promotion boundary defects during
  the first pass: unmapped tables were outside the final preservation check,
  RBAC verb variants could share and reuse a v1 operation, and an accepted
  five-column non-resource addition could lose its URL when written into a
  legacy table. The repaired path now checks all Markdown table rows, uses
  verb-aware internal identities with conservative ambiguous-operation
  rejection, consumes operations at most once, and upgrades legacy output
  headers without inventing URL facts.
- Final author verification passed 93 focused promotion/merge/phase tests, 948
  repository-wide tests with 10 skips, `make test` (269 Python tests with four
  skips plus all Go modules), Ruff, Go lint/vet, 31 overlays, 18 platforms, and
  all 901 tracked component documents. The independent reviewer passed 118
  targeted tests, every Go module suite, exact recorded replay reproduction,
  `git diff --check`, and the tracked-architecture guard with no remaining
  correctness findings.

Repair the two promotion defects exposed by the repeated `rhods-operator`
architecture-surface canary while preserving the rejected canary artifacts as
immutable evidence.

## Scope

- Preserve resource and non-resource RBAC permissions through analyzer
  extraction, rendering, Python parsing and identity, evidence-gated merge, and
  arch-doc assembly. Retain non-resource URLs when known, keep their identities
  distinct from resource rules, and handle legacy rows without URL facts
  conservatively.
- Detect every analyzer baseline row lost from final output, including rows the
  normalized architecture parser cannot represent, and include those failures
  in merge accounting and durable run reports.
- Detect configured synthesis subsections outside their permitted parent, reject
  them without relocation, and propagate an actionable assembly failure through
  the runner and retained merge/run diagnostics.
- Replay all four saved canary candidates offline into a separate repair result;
  never modify the original retained canary evidence or tracked architecture.

## Verification

- Add loss-reproducing regressions before the repair and positive/negative
  coverage for resource, non-resource, and legacy RBAC rows.
- Cover correctly placed and misplaced configured synthesis subsections and
  durable failure propagation.
- Run focused and preservation tests, replay all four retained runs, then run
  repository test and lint gates.
- Obtain a fresh independent Sol review, address findings, and rerun affected
  checks.

## Boundaries

Do not launch live generation agents, regenerate the platform corpus, edit
tracked architecture documents, change warning-only coverage, enable component
workers, mutate original canary evidence, or commit changes.

## Related bugs

- [Promotion Drops Analyzer Non-Resource RBAC Rows](../../bugs/fixed/promotion-drops-analyzer-non-resource-rbac-rows.md)
- [Merge Report Omits Candidate Section Loss](../../bugs/fixed/merge-report-omits-candidate-section-loss.md)

## Remaining limitations

- The saved replay covers one component and four historical candidates. Generic
  parser and preservation regressions cover additional table shapes, but no
  broader platform corpus was regenerated.
- The v1 RBAC patch key intentionally remains three cells for compatibility.
  When multiple verb variants share that key, the operation is rejected as
  ambiguous; a future patch schema can add a more specific identity.
- Section placement diagnostics cover every synthesis subsection configured in
  the arch-doc manifest. New subsection kinds must be added to that manifest to
  receive the same ownership check.
