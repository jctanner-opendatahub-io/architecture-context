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

Live agent runs were cancelled by user direction and are outside this canary.
Consequently the decision is provisional: the on-disk outputs are single,
complementary observations and cannot establish variability, repeat reliability,
latency, cost, token/cache use, read ranges, discovery calls, preservation, or
merge behavior. Follow `source-review.md` when updating either pinned comparison.

Missing runtime measurements remain `null`; the report does not infer them from
document size or mix them with deterministic replay values.

## On-disk rollout audit

`audit_tree.py` inventories the component documents and stored analyzer
artifacts currently present under `architecture/`. It reads no source checkout,
pipeline log, agent transcript, or external service, and it does not edit the
generated tree. Run it with:

```bash
uv run python evaluations/architecture-surface-coverage/audit_tree.py \
  --architecture-root architecture \
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
