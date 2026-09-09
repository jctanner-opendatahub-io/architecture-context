# Structured component final offline evidence

This directory contains the P5 offline evidence candidate. It does not contain
a new live-model result and does not authorize rollout.

- `preservation-check.json` verifies the 76-path historical manifest with the
  one independently accepted formatting exception: 75 original paths are
  unchanged, the original comparison source is retained separately, and the
  formatted comparison source has its recorded current hash.
- `offline-canary-replay/` is a test-only analyzer conversion in a new output
  tree. It does not convert model-authored candidate Markdown. Three legacy
  candidates pass the structural FIPS placement check; the malformed fourth
  candidate produces `malformed-legacy-fips-placement`. Every synthesis
  envelope says `historical-response-missing`, every run records zero model
  calls, and the original canary remains rejected.
  The resulting schema-1.0 documents are private normalization evidence, not
  accepted published schema-1.1 authorities; P4's separately reviewed
  publication tests cover that upgrade and its durable bindings.
- `reuse-comparison.json` is the preserved interim saved-row recount. Its
  statement that the 92 exact source pairs were unavailable is false and is
  superseded; the file stays byte-identical so the rejected claim remains
  auditable.
- `fresh-reuse/results.json` summarizes the actual fresh extraction. All 184
  sides were materialized from their recorded committed trees and all 92 pairs
  were compared by unchanged `compare.py`. The old committed build produced
  31/37 in attempt 3 and 30/36 in the independent rerun because set-like
  producer ordering varied. The repaired build produced stable 32/38 results
  in two independent 184-side runs. Verified reuse remains zero because
  producing/search/synthesis context is absent.
- `sc24-measurements.json` separates historical pipeline telemetry, current
  offline operations, and implementation/review harness use.
- `requirements-matrix.json` is the implementer's proposed SC-01--SC-25 final
  matrix. It awaits the separately dispatched independent P5 review.

Reproduce the executable evidence with:

```bash
GOCACHE=/tmp/structured-component-final-go-cache \
  go -C src/arch-analyzer build \
  -o /tmp/structured-component-final-20260909/arch-analyzer .
UV_CACHE_DIR=/tmp/structured-component-final-uv-cache uv run python \
  scripts/structured_component_final_evidence.py verify-preservation \
  --output /tmp/preservation-check.json
UV_CACHE_DIR=/tmp/structured-component-final-uv-cache uv run python \
  scripts/structured_component_final_evidence.py replay-canary \
  --output-dir /tmp/offline-canary-replay \
  --arch-analyzer /tmp/structured-component-final-20260909/arch-analyzer
UV_CACHE_DIR=/tmp/structured-component-final-uv-cache uv run python \
  scripts/structured_component_final_evidence.py compare-reuse \
  --output /tmp/reuse-comparison.json \
  --arch-analyzer /tmp/structured-component-final-20260909/arch-analyzer \
  --build-command \
  'GOCACHE=/tmp/structured-component-final-go-cache go -C src/arch-analyzer build -o /tmp/structured-component-final-20260909/arch-analyzer .'
```

The old-build fresh run uses the `fresh-compare-reuse` subcommand. Its exact
command, three-attempt lineage, raw JSON, stdout/stderr, timings, source
identities, pair fingerprints, and build verification are retained under
`logs/structured-component-assembly/20260909-fresh-reuse/`. The repaired build,
source manifest/diff, two independent full extractions, ordering/content
comparison, and P1 render impact are retained separately under
`logs/structured-component-assembly/20260909-ordering-repair/`. None of these
runs executed checkout filters, repository scripts, a model, or the pipeline.

Use a fresh, nonexistent replay directory. The command refuses an existing
directory so reruns cannot overwrite original or prior evidence.
