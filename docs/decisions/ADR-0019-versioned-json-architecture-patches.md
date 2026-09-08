# ADR-0019: Use Versioned JSON Architecture Table Patches

## Status

Accepted

## Date

2026-09-05

## Context

Readiness-routed component generation preserves analyzer-owned Markdown tables
and lets an agent request exact, evidence-backed additions, updates, or
deletions. The original request artifact was an agent-authored Markdown table.
Real runs produced prose-only files, malformed table categories and values, and
incorrect compound keys even when the candidate document contained useful
source-backed rows. The merge correctly rejected those rows, but the formatting
contract caused avoidable loss before evidence adjudication.

## Decision

Make `ARCHITECTURE_PATCH.json` the required structured-change artifact for new
evidence-gated runs. Version 1 contains an `operations` array. Every operation
names its action, architecture category, ordered key tuple, target column, exact
cell values, reason, and repository-relative numeric evidence.

Validate the artifact against
`schemas/architecture-table-patch-v1.schema.json` at the merge boundary. Apply
dynamic route policy after schema validation so an otherwise valid category is
still rejected when it falls outside the component's readiness gap budget.
Require exact candidate/analyzer identity and cell-value matches. Invalid or
unmatched JSON operations produce actionable diagnostics and prevent the final
merged document from being written or promoted.

Keep the Markdown change-record parser and `--changes` replay option for
historical artifacts. New orchestration uses `--patch-output` and archives
`<component>.patch.json`. Narrative synthesis remains in the preseeded candidate
Markdown and final tables continue to be rendered by the orchestrator.

## Consequences

- Agents no longer need to construct an exact Markdown authorization table.
- Compound keys, action-specific null values, categories, columns, reasons, and
  evidence receive deterministic validation before promotion.
- Analyzer rows remain authoritative unless an exact authorized operation
  applies.
- Empty operation arrays explicitly represent a run with no requested table
  changes; a missing patch artifact is a generation failure.
- Historical Markdown replays continue to work during migration, while the
  generation path has one JSON default.
- JSON Schema is a runtime dependency of the merge boundary.
