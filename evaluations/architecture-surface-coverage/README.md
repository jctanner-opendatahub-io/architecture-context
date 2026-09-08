# Architecture Surface Coverage Evaluation

This directory contains the durable, source-reviewed canary for
`red-hat-data-services/rhods-operator` at
`4ada791819c522a4cda54f9029ab3e4056ed31ed`.

`experiment.json` pins the source, analyzer and skill fingerprints, expected
surface claims, gates, and an ordered one-factor-at-a-time condition sequence.
`replay-results.json` records two deterministic fixture replays per condition.
These records are measurement metadata, not architecture synthesis inputs.
They contain no source excerpts, historical document text, or agent transcript.

Generate and validate the durable report without an agent:

```bash
uv run python evaluations/architecture-surface-coverage/evaluate.py \
  --manifest evaluations/architecture-surface-coverage/experiment.json \
  --results evaluations/architecture-surface-coverage/replay-results.json \
  --output-json evaluations/architecture-surface-coverage/report.json \
  --output-markdown evaluations/architecture-surface-coverage/report.md
```

The fixture replay establishes deterministic scoring and decision behavior. It
does not represent model repetitions. The observed comparison is limited to the
two SHA-256-pinned `rhods-operator.md` files under `architecture/`, scored
against the source claims in `experiment.json`. Those files are comparison-only
and are never passed into synthesis.

Live agent runs are outside this offline canary. Its on-disk outputs remain
single, complementary observations and do not establish variability, repeat
reliability, latency, cost, token/cache use, read ranges, discovery calls,
preservation, or merge behavior. Follow `source-review.md` when updating either
pinned comparison.

Missing runtime measurements remain `null`; the report does not infer them from
document size or mix them with deterministic replay values.

## Repeated live canary

The separately authorized live comparison is retained under `live-canary/`.
It contains two sequential `rhods-operator` repetitions for each exact model,
the identical refreshed inputs, promoted and candidate documents, sidecars,
merge and run telemetry, a source review, and a hash manifest. Raw agent
transcripts are not retained.

The operator-run preflight recorded `claude-opus-4-6` through first-party
`claude.ai` authentication. Every Claude launch explicitly removed
`CLAUDE_CODE_USE_VERTEX`, `ANTHROPIC_VERTEX_PROJECT_ID`, and
`CLOUD_ML_REGION`; Codex requested `gpt-5.6-sol`. The hash manifest pins the
requested model IDs and per-run telemetry. The retained set has no hashed
provider-preflight transcript or service-signed model attestation, so those
launch records cannot be independently re-attested from durable artifacts.
Per-run manifests record that historical summaries were excluded from synthesis,
but raw prompts and transcripts were not retained.

Reproduce the reviewed report without an agent or source checkout:

```bash
uv run python evaluations/architecture-surface-coverage/evaluate_live.py \
  --manifest evaluations/architecture-surface-coverage/live-canary/manifest.json \
  --source-review evaluations/architecture-surface-coverage/live-canary/source-review.json \
  --output-json evaluations/architecture-surface-coverage/live-canary/report.json \
  --output-markdown evaluations/architecture-surface-coverage/live-canary/report.md
```

The report scores final promoted documents, records candidate-to-promoted loss,
and keeps source-reviewed recall separate from model-authored coverage sidecars.
It rejects the canary because all four promoted documents lost two
analyzer-rendered RBAC rows; Codex passed the full source-review gate in one of
two repetitions and Claude passed neither. The historical files remain
comparison-only and are not a matched live baseline. Independent review
accepted the corrected source review, evaluator, and report on 2026-09-06; this
accepts the evidence record, while the canary outcome remains rejected.

## On-disk rollout audit

`audit_tree.py` inventories the component documents and stored analyzer
artifacts currently present under `architecture/`. It reads no source checkout,
pipeline log, agent transcript, or external service, and it does not edit the
generated tree. Run it with:

```bash
uv run python evaluations/architecture-surface-coverage/audit_tree.py \
  --architecture-root architecture \
  --comparison-baseline evaluations/architecture-surface-coverage/rollout-audit-fips-baseline.json \
  --output-json evaluations/architecture-surface-coverage/rollout-audit.json \
  --output-markdown evaluations/architecture-surface-coverage/rollout-audit.md
```

The audit excludes symlinked platform aliases and fingerprints the physical
inputs. It separates three generation cohorts. Pre-3.6 documents used an
external `architecture-analyzer`, while the LLM retained full control of the
summary. Project `arch-analyzer` pairs begin in the 3.6 era. Documents in 3.6 or
rolling directories without a stored project analyzer remain unclassified.
Legacy documents are not reported as missing project-analyzer outputs or used
as equivalent coverage baselines.

A missing legacy coverage sidecar means disposition and read telemetry is
unavailable; it is not classified as a behavioral omission. Exact analyzer
records, precise unresolved records, generic gap candidates, and document path
mentions also remain separate. A path mention is only a structural signal and
does not establish semantic coverage.

The comparison baseline pins the pre-fix report from commit `39209078`. The
audit accepts it only when the architecture input fingerprint matches, then
reports the FIPS planning-rule nomination delta. A decrease in nominations does
not establish improved semantic recall.

## Analyzer refresh input manifest

`plan_refresh.py` turns the audit's representative set into a deterministic
preflight for a future analyzer refresh while respecting the architecture-only
boundary:

```bash
uv run python evaluations/architecture-surface-coverage/plan_refresh.py \
  --architecture-root architecture \
  --rollout-audit evaluations/architecture-surface-coverage/rollout-audit.json \
  --output-json evaluations/architecture-surface-coverage/refresh-input-plan.json \
  --output-markdown evaluations/architecture-surface-coverage/refresh-input-plan.md
```

The manifest puts `rhods-operator` first, then selects the deterministic
operator/service/manifest cohort. It verifies source identities against the
stored analyzer JSON, rejects non-exact commits and stale audit hashes, and
fingerprints every stored analyzer output and comparison document. It does not
read source checkouts, run the analyzer, substitute revisions, or write below
`architecture/`. An unavailable source input is recorded as unavailable rather
than treated as refreshed evidence.

## Completed analyzer refresh

After the exact platform checkouts became available, the nine artifacts were
rebuilt in an isolated `/tmp` architecture root with the standard
`static-analysis` phase. `refresh-result.json` records clean checkout origins
and HEADs, the analyzer base revision and source-diff fingerprint, binary and
component-map hashes, extraction configuration, structured-output hashes,
render/context hashes, and 157 schema outputs. The structured JSON needed to
reproduce the audit is retained under `refreshed-analyzers/`; generated
architecture was not changed.

The first run exposed that current zero-record outputs still omitted
`behavioral_evidence`, making them indistinguishable from pre-extractor legacy
artifacts. The encoder now emits an empty array for current zero-record results
while legacy decode remains compatible. The final refresh contains three
`present-records` and six `present-empty` artifacts. Its 43 behavioral records
contain three source-reviewed observations in `rhods-operator` and 40 precise
unresolved questions across the three Go operators.

Record a completed isolated run with:

```bash
uv run python evaluations/architecture-surface-coverage/record_refresh.py \
  --input-plan evaluations/architecture-surface-coverage/refresh-input-plan.json \
  --architecture-root architecture \
  --refreshed-root /tmp/architecture-surface-refresh \
  --checkout-root checkouts/red-hat-data-services.rhoai-3.6-ea.2 \
  --checkout-root checkouts/llm-d.rhoai-3.6-ea.2 \
  --analyzer-binary bin/arch-analyzer \
  --output-dir evaluations/architecture-surface-coverage/refreshed-analyzers \
  --output-json evaluations/architecture-surface-coverage/refresh-result.json \
  --output-markdown evaluations/architecture-surface-coverage/refresh-result.md
```

Reproduce the refreshed audit without source checkouts or temporary analyzer
outputs with:

```bash
uv run python evaluations/architecture-surface-coverage/audit_refreshed.py \
  --refresh-result evaluations/architecture-surface-coverage/refresh-result.json \
  --architecture-root architecture \
  --output-json evaluations/architecture-surface-coverage/refreshed-rollout-audit.json \
  --output-markdown evaluations/architecture-surface-coverage/refreshed-rollout-audit.md
```

The refreshed audit remains structural. It establishes analyzer capability and
precise evidence records for this cohort; it does not establish generated-
summary recall, warning false-positive rates, agent preservation, or live-run
cost and reliability.

An independent Sol review accepted the refresh and encoder correction with no
blocking findings. It independently verified all nine pinned clean checkouts,
recomputed the analyzer provenance, rebuilt a byte-identical binary, checked the
three observed source facts and 40 unresolved records, and reproduced the JSON
and Markdown audit files byte-for-byte. An optional independent full
`rhods-operator` static-analysis rerun was stopped after several quiet minutes,
so that review did not separately regenerate the 130-schema bundle or rendered
output hashes.

A normalized same-document cohort check kept 41 nominated surfaces, 24 required
surfaces, 17 high-priority surfaces, and all nine uncertain runtime-FIPS
nominations unchanged. Behavioral evidence changed from nine `field-absent`
artifacts and zero records to three `present-records`, six `present-empty`, and
43 records. Generic gap candidates increased from 297 to 388 as the refreshed
analyzer retained more explicit questions. These are analyzer-output deltas,
not evidence of generated-summary recall.
