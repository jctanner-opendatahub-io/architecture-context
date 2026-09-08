# Architecture Surface Coverage Completion Audit

Date: 2026-09-05

This audit checks the execution state of
[`architecture-surface-coverage.md`](../plans/architecture-surface-coverage.md).
The source-only analyzer refresh and repeated live canary were subsequently
authorized. Generated architecture was not modified.

## Execution state

| Plan item | State | Evidence |
|---|---|---|
| Source-verified fixtures and coverage contract | Complete | [Implementation task](../tasks/done/improve-architecture-surface-coverage.md) |
| Surface planning, synthesis review, and promoted-document validation | Complete | [Implementation task](../tasks/done/improve-architecture-surface-coverage.md) |
| Behavioral analyzer extraction | Complete for the implemented fixtures | [Implementation task](../tasks/done/improve-architecture-surface-coverage.md) |
| Offline canary and on-disk comparison | Complete with documented measurement limits | [Evaluation report](../../evaluations/architecture-surface-coverage/README.md) |
| Existing-tree rollout audit | Complete | [Audit task](../tasks/done/audit-architecture-surface-rollout.md) |
| FIPS applicability correction | Complete and independently accepted | [FIPS task](../tasks/done/fix-surface-fips-applicability.md) |
| Repository validation baseline | Complete | [Checkpoint task](../tasks/done/checkpoint-surface-work-and-restore-validation.md) |
| Analyzer artifact refresh | Complete and independently accepted | [Refresh task](../tasks/done/refresh-surface-analyzer-evidence.md) |
| Repeated live canary | Complete; independently reviewed report rejects canary on promotion preservation | [Live-canary task](../tasks/done/run-surface-coverage-live-canary.md) |
| Enforcement and worker decisions | Complete: warning-only and workers disabled | [ADR-0023](../decisions/ADR-0023-keep-surface-coverage-warning-only.md) |
| Versioned JSON Patch contract | Complete | [ADR-0019](../decisions/ADR-0019-versioned-json-architecture-patches.md) |
| Deterministic version index | Complete without generating repository data | [ADR-0024](../decisions/ADR-0024-deterministic-version-navigation-index.md) |

## Live-canary correction

The exact repositories were found at all nine pinned commits and refreshed in
an isolated output root. The completed record pins the analyzer base, source
diff, full source tree, binary, configuration, checkouts, and output hashes.
It contains three source-observed and 40 precise unresolved behavioral records;
six zero-record artifacts explicitly encode `behavioral_evidence` as an empty
array. Independent review accepted the source facts, encoder correction, and
byte-reproducible audit with no blocking findings.

The authorized canary ran twice per requested exact model. The four agent
processes completed within the approved envelope and retained hash-identical
input copies. The first independent report review found two missed unsupported
claims and found that all four promoted documents silently lost the same two
analyzer-rendered RBAC rows. The corrected evaluator reproduces those losses,
marks all four promotions failed, records Codex at one of two full source-review
passes and Claude at zero of two, and rejects the canary. Independent re-review
accepted that correction after the source basis was updated to the pinned
controller-runtime `v0.24.1` and dependency-version matching was regressed. The
warning-only decision and disabled worker policy remain in effect.

## Validation

The final local revision passes the full Python suite (917 passed, 10 skipped),
`make test`, `make lint`, nine focused live-canary tests, Ruff, and byte-for-byte
live-report reproduction. The refreshed audit JSON hash is
`891dc372ff674fde9f712befd3b6adf0db2b1b9b55c76909792c93279c830a6a`;
its Markdown hash is
`02d12538cc10a92edb14210ad91c564b392dec0e0d7c8f737bd273b5585c3640`.
There is no tracked diff below `architecture/`.
