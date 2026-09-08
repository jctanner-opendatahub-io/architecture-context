# Repeated Live Architecture Surface Canary

## Result

All 4 isolated agent runs completed at the recorded pinned source revision with the requested exact models and hash-identical retained inputs. The canary is rejected because every promoted document lost two analyzer-rendered RBAC rows. Coverage remains warning-only and subsection workers remain disabled.

The operator-run Claude preflight recorded first-party `claude.ai` authentication, and `CLAUDE_CODE_USE_VERTEX`, `ANTHROPIC_VERTEX_PROJECT_ID`, and `CLOUD_ML_REGION` were explicitly removed from each launch. The durable artifact set does not include a hashed per-run provider-preflight transcript, so it cannot independently re-attest the provider after the run.

## Repeated source review

| Harness | Exact model | Surface recall | Claim recall | Unsupported claims | Runs passing gate |
|---|---|---:|---:|---:|---:|
| claude | `claude-opus-4-6` | 0.500 | 0.643 | 6 | 0/2 |
| codex | `gpt-5.6-sol` | 1.000 | 1.000 | 1 | 1/2 |

| Surface | Claude | Codex |
|---|---|---|
| `authentication.gateway-modes` | partial, partial | supported, supported |
| `authentication.metrics-enforcement` | supported, supported | supported, supported |
| `compliance.runtime-fips` | unsupported, omitted | supported, supported |
| `controller.named-resource-watches` | supported, supported | supported, supported |

Claude recalled conditional metrics enforcement and both literal namespace watches in both runs. Neither Claude run fully represented integrated OAuth, external OIDC, and externally managed authentication. Repetition 1 promoted unsupported FIPS, linkage, and gateway-proxy claims; repetition 2 authored a FIPS section in the candidate, but final assembly removed it.

Both Codex runs represented all seven required claims across the four surfaces and explicitly stated that build and TLS signals do not establish runtime FIPS compliance. Repetition 1 also made an unsupported initialization-ordering claim outside those four required surfaces, so only Codex repetition 2 passed the zero-unsupported-claim gate.

## Run measurements

| Run | Duration | Files | Budget delta | Merge | Warnings | Surface recall | Unsupported | Usage |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `claude-repetition-1` | 377.6s | 7 | +1 | 1 applied/0 rejected/0 restored | 12 | 0.500 | 6 | $1.8399 |
| `claude-repetition-2` | 443.8s | 6 | +0 | 1 applied/0 rejected/0 restored | 16 | 0.500 | 0 | $1.9287 |
| `codex-repetition-1` | 283.3s | 5 | +0 | 0 applied/0 rejected/0 restored | 6 | 1.000 | 1 | 1,004,455 tokens |
| `codex-repetition-2` | 300.2s | 7 | +1 | 0 applied/0 rejected/0 restored | 10 | 1.000 | 0 | 1,406,138 tokens |

Claude aggregate cost was `$3.7686` against the approved `$40` aggregate cap. Codex reported `2,410,593` cumulative tokens across its two single-turn runs. Codex command telemetry does not classify its `rg` discovery calls separately, so the retained zero discovery count is an instrumentation limit rather than proof of no search.

## Warning and promotion quality

The validator emitted 44 messages: 28 sidecar-contract diagnostics, 4 useful semantic signals, and 12 confirmed false positives (27.3%). The false positives mostly reported missing document references even when source-reviewed content was present.

Every promoted document lost the analyzer-rendered `opendatahub-operator-metrics-reader` and `metrics-reader` RBAC rows, for eight lost row occurrences across four runs. The merge reports still recorded 274 unchanged rows and zero restorations because those two rows were outside the parser's accounted set. Claude repetition 2 also lost `compliance.runtime-fips` between candidate and promoted output. Its coverage validator detected that surface omission, but the merge report did not. These are promotion failures under the approved stop conditions.

The two Claude patches each applied one evidence-backed metrics authentication row; both Codex patches were empty.

## Provenance limits

Requested model IDs and runner telemetry are pinned; the retained artifacts do not contain a service-signed model-identity attestation.

Per-run input manifests record that historical summaries were not synthesis inputs, but no full prompt or raw transcript was retained.

## Decision

The canary is rejected because promotion failed in 4 of 4 runs: final output lost 8 analyzer-row occurrences. Codex passed the source-review gate in 1 of 2 repetitions and Claude passed in 0 of 2; 3 sidecars were structurally invalid and 12 of 44 warnings were confirmed false positives.

This result does not change rollout policy. Coverage stays warning-only, subsection workers stay disabled, and historical outputs remain comparison-only because they are not a matched live baseline.
