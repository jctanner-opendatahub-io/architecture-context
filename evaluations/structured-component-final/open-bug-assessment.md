# P5 open-bug assessment

This is an implementer recommendation only. The coordinator owns bug-file and
ledger transitions.

## Acceptance criteria now met

`reuse-target-integration-status-needs-producer-binding.md` can be closed after
the independent P5 reviewer confirms the final bytes. The production seam
imports `lib.version_index._resolve_integration` and, for every selected
component, derives the target status from the current raw component-map entry,
current platform configuration, and active overlays before constructing the
synthesis request (`lib/structured_component_synthesis.py:3081,3142-3147`).
It does not accept that status from the model or reuse invariant.

`test_pipeline_seam_persists_reloads_and_reuses_with_actual_go` changes the
current target component-map status from the predecessor's value to `current`,
reuses with no additional synthesis call, and verifies that the current
document carries `current` plus the refreshed source revision
(`tests/test_structured_component_synthesis.py:1681-1770`). P3/P4 independent
reviews accepted these unchanged production/test bytes. The P5 full test run
and reviewer still need to confirm the final working tree.

## Remain open and nonblocking

- `codex-discovery-telemetry-misses-rg.md` and
  `codex-reuse-live-wrapper-limitations.md`: live Codex search/read evidence is
  incomplete. SC-25 therefore requires a miss; this packet records zero
  verified legacy reuse.
- `reuse-noncanonical-number-literals-cause-miss.md`: conservative miss only;
  no false hit and no hit-rate promise.
- `structured-publication-markdown-repair-races-replacement.md`: mismatch is
  detected and recoverable, but the inspected race remains backlog.
- `structured-publication-no-repair-flag-still-recovers.md`: API-clarity issue;
  recovery remains safe.
- `structured-query-number-canonicalization-diverges.md`: query/reuse numeric
  canonicalization difference remains backlog.
- `surface-coverage-document-reference-false-positives.md`: warning accuracy
  remains imperfect. Coverage is still warning-only.

None of these open findings is converted into a measured quality or reuse
claim. SC-24 live evidence remains unimplemented and adoption remains HOLD.

`structured-analyzer-ordering-causes-spurious-reuse-misses.md` has a direct
producer repair and complete local evidence, but remains coordinator-owned and
open pending independent P5 review cycle 2. The repaired binary produced
identical relevant outputs across two independent 184-side runs; an actual
extractor-to-reuse test makes zero extra synthesis calls for identical inputs.
All old-to-repaired changes in the four affected fields are ordering-only, and
meaningful-order invalidation remains in the reuse contract.

## Coordinator-owned P5 comparison bug

`structured-final-reuse-comparison-skips-available-sources.md` now has
implementation evidence for its acceptance criteria: 184/184 committed source
sides were freshly extracted, unchanged `compare.py` saw all 92 pairs, and the
false source-absence claim is superseded without rewriting its interim report.
The final P5 independent reviewer must still inspect the utility, attempt
lineage, raw outputs, and counts. The coordinator therefore retains ownership
of closing the bug after that review; this implementer does not change its
status.

The old-build counts remain observed variance: 31/37 in attempt 3 and 30/36 in
the reviewer's rerun. The repaired build's independently repeated result is
32/38. kube-rbac-proxy's old cross-version miss was an import-map ordering
artifact. `models-perf-benchmark-data` is different: its historical comparison
used a dirty working tree, while fresh evidence used the committed tree, so its
`scan_statistics` difference is not attributed to ordering or repaired away.
