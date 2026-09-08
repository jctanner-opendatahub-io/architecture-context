# Task: Replace Markdown Change Records with a JSON Patch Contract

## Goal

Make evidence-gated architecture merges deterministic by replacing the
agent-authored Markdown change table with a validated machine-readable patch
artifact.

## Context

The partial-route agent can produce correct source-backed rows in its candidate
document while formatting `ARCHITECTURE_CHANGES.md` incorrectly. In the
`odh-gitops` full run, 31 candidate rows were rejected because the sidecar was
prose-only. A follow-up replay emitted the table but still produced malformed
categories, values, and compound keys. The current Markdown parser correctly
protects the analyzer baseline, but the contract is too fragile for repeated
agent use.

## Proposed Design

- Agent emits a JSON patch sidecar containing category, key tuple, action,
  cell values, reason, and repository-relative evidence.
- JSON schema validation rejects unsupported categories, malformed key tuples,
  missing reasons, invalid evidence, and unauthorized gap categories before
  merge.
- Orchestrator applies valid patches to the analyzer baseline and renders the
  final Markdown tables deterministically.
- Narrative sections remain agent-authored and continue to use the preseeded
  candidate document.
- Preserve the current Markdown sidecar as a compatibility reader during
  migration, if existing historical artifacts require it.

## Scope

- Define and validate a versioned JSON patch schema.
- Add a deterministic patch application/rendering boundary.
- Update the summary skill and agent prompt contract.
- Add malformed-patch, compound-key, evidence, and migration tests.
- Measure whether rejected candidate-row and quality-gate failures decrease on
  the targeted replay before considering a broader rollout.

## Non-Goals

- Do not weaken analyzer-baseline preservation or evidence requirements.
- Do not hardcode `odh-gitops` rows or component-specific exceptions.
- Do not remove agent-authored narrative synthesis.

## Acceptance Criteria

- A valid JSON patch applies the intended evidence-backed rows without manual
  Markdown formatting.
- Invalid patches fail with actionable diagnostics before final merge.
- Existing analyzer rows remain authoritative unless an authorized patch
  updates them.
- Targeted and focused tests pass, and the `odh-gitops` replay no longer loses
  valid candidate rows at merge time.

## Status

Complete on 2026-09-05. New evidence-gated runs require
`ARCHITECTURE_PATCH.json`; JSON Schema and semantic validation run at the merge
boundary, invalid or unmatched operations prevent final output, and the
Markdown reader remains available only for historical replay.

The durable sanitized `odh-gitops` fixture applies five representative
evidence-backed additions across architecture components, internal
dependencies, authentication, and integration points with zero rejected or
restored rows. It reads no pipeline log, source checkout, or generated
architecture during the test.

Validation: repository-wide pytest passed 843 tests with nine skips; focused
merge, phase, guard, skill, routing, and replay coverage passed 172 tests;
`make test` passed 262 Python tests with four skips plus every Go module; Ruff,
Go lint/vet, lockfile validation, 31 overlays, 18 platforms, 901 architecture
documents, and `git diff --check` passed.
