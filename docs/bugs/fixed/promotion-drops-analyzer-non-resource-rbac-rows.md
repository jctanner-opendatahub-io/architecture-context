# Bug: Promotion Drops Analyzer Non-Resource RBAC Rows

## Status

Fixed and independently accepted 2026-09-06.

All four repeated `rhods-operator` live-canary runs lost these analyzer-rendered
cluster-role rows during final promotion:

```markdown
| opendatahub-operator-metrics-reader |  |  | get |
| metrics-reader |  |  | get |
```

Both rows appear in the retained analyzer preseed and every agent candidate,
but neither appears in any promoted document. The source role is a valid
non-resource role for `/metrics` at
`config/rbac/auth_proxy_client_clusterrole.yaml:1-9` in the pinned checkout.

The merge reports still claim 274 unchanged rows and zero restorations. The
RBAC row identity requires role name, API group, and resources; the parser
normalizes the empty API group to `<core>` but rejects the empty resource cell,
so these non-resource RBAC rows fall outside merge accounting and preservation.

Evidence is retained in the repeated
[live-canary report](../../../evaluations/architecture-surface-coverage/live-canary/report.md)
and its four `preseed.md`, `candidate.md`, `promoted.md`, and `merge.json`
artifact sets.

Expected behavior: analyzer-rendered non-resource RBAC facts must have a stable
identity that retains the non-resource URL, survive protected final assembly,
and participate in merge accounting. Promotion must fail with an actionable
diagnostic if any analyzer-owned row is omitted.

## Root cause

The analyzer input and rendered row model discarded Kubernetes
`nonResourceURLs`. The Python table parser then required a resource-based key,
so the legacy four-column rows with empty resource cells were outside merge
accounting. Final preservation checked only mapped, representable tables, which
left these rows and any unknown table shape vulnerable to silent assembly loss.

## Resolution

The analyzer now extracts, normalizes, and renders non-resource URLs in a
dedicated fifth column. Python assigns disjoint resource, non-resource, mixed,
and conservative legacy target keys. Internal RBAC matching also includes verbs
while the persisted v1 three-cell patch key remains compatible. A v1 operation
that could match multiple verb variants is rejected, and each operation can be
consumed only once.

Legacy rows retain only facts they contain. When a source-backed candidate adds
a URL fact to a legacy table, promotion upgrades the output to the five-column
schema; it never guesses a URL for an existing four-column row. Arch-query and
the skill validator accept current and legacy forms.

Final assembly compares every adjudicated Markdown table row, including opaque
mapped rows and wholly unmapped tables. A loss fails promotion with
`analyzer_row_lost_during_assembly` and persists the missing row details.

## Verification

The separate [promotion repair replay](../../../evaluations/architecture-surface-coverage/promotion-repair-replay/report.md)
preserves 276/276 mapped rows and 310/310 total analyzer table rows in every
saved run. The original live-canary evidence remains immutable and rejected.
Positive, negative, legacy, identity-collision, ambiguous-operation, table
upgrade, parser, renderer, query, and assembly-loss regressions pass. A fresh
Sol review accepted the fix with no remaining correctness findings.
