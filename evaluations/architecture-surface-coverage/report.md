# Architecture Surface Coverage Canary

Pinned source: `red-hat-data-services/rhods-operator@4ada791819c522a4cda54f9029ab3e4056ed31ed`.

Two repeated deterministic source-fixture replays per condition. Recall, uncertainty, preservation, merge, and read metrics are replay observations; agent latency, cost, and token values are unavailable and remain null.

| Condition | Repeats | Recall (min/mean) | Unsupported max | Unresolved max | Preserved min | Merge lost | Files / ranges | Discovery mean | Latency mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 2 | 0.50 / 0.50 | 0 | 0 | 1.00 | 0 | 3 / 3 | 0.0 | unavailable |
| surface-planning-review | 2 | 0.75 / 0.75 | 0 | 1 | 1.00 | 0 | 4 / 4 | 0.0 | unavailable |
| behavioral-extraction | 2 | 1.00 / 1.00 | 0 | 0 | 1.00 | 0 | 2 / 2 | 0.0 | unavailable |
| surface-aware-budget | 2 | 1.00 / 1.00 | 0 | 0 | 1.00 | 0 | 2 / 2 | 0.0 | unavailable |

## Measurement limits

- Each observed architecture file is a single output, so the comparison cannot estimate model variability or repeat reliability.
- The architecture files do not contain comparable latency, cost, token, cache, source-read-range, or discovery-call telemetry.
- Analyzer preservation and merge rejection/loss cannot be reconstructed from the architecture files alone.
- The staged condition results are deterministic source-fixture replays, not observed model runs; their null runtime values must not be imputed.

Execution notes:

- Live-agent execution was cancelled and is unavailable under the user-directed offline constraint; no live result is scored.

## Observed on-disk comparison

| Harness / model | Recall | Unsupported | Artifact SHA-256 | Artifact | Limitation |
|---|---:|---:|---|---|---|
| claude / claude-opus-4-6 | 0.50 | 3 | `458bdc321a7951979b23bd8bc6fc33986cdbd415f2763378c5b2d472af322eea` | `architecture/rhoai-3.6-ea.2.claude/rhods-operator.md` | Single on-disk output with no comparable run telemetry; gateway modes are incomplete and FIPS/package/linkage claims exceed the pinned source. |
| codex / gpt-5.6-sol | 0.50 | 0 | `5cfbf54d76aca7fa8afdb0988eecdf90a36d679f7513498290241efa21df7ebc` | `architecture/rhoai-3.6-ea.2/rhods-operator.md` | Single on-disk output with no comparable run telemetry; it omits conditional metrics enforcement and named Namespace-watch semantics. |

| Harness | Metrics enforcement | Named watches | Gateway modes | Runtime FIPS |
|---|---|---|---|---|
| claude | supported | supported | partial | unsupported |
| codex | omitted | omitted | supported | supported |

Source-refuted claims:

- claude: The component has FIPS-compliant builds or full FIPS compliance signals. The selected CSV marks features.operators.openshift.io/fips-compliant false; strictfipsruntime and CGO flags do not establish runtime compliance.
- claude: The UBI base declaration proves that OpenSSL with post-quantum support is present in the produced runtime image. The Dockerfile base reference alone is not a verified runtime package inventory.
- claude: CGO_ENABLED=1 ensures dynamic OpenSSL linkage and Go crypto/tls operates through OpenSSL in FIPS mode. Neither the source nor an inspected binary/provider state establishes those linkage and provider claims.

These architecture files were reviewed only for comparison and were never provided to synthesis runs.

## Decision

Provisional condition: `behavioral-extraction`.

Deterministic fixtures make behavioral extraction the earliest passing condition; the two single on-disk outputs have complementary supported surface sets (claude 0.50; codex 0.50), so repeated controlled evidence is still required before rollout.

Subsection workers remain disabled and coverage validation remains warning-only. Worker adoption and global enforcement require a separate rollout decision.

Runtime token, cost, latency, read, and variability measurements remain unavailable under the current no-live-agent constraint.
