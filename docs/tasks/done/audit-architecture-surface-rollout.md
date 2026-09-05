# Task: Audit Architecture Surface Rollout

## Status

Done 2026-09-05.

## Goal

Measure architecture-surface warning quality and analyzer evidence capability
across the existing on-disk architecture corpus before considering broader
enforcement.

## Scope

Follow phase 6 of the
[Architecture Surface Coverage plan](../../plans/architecture-surface-coverage.md).
Use only component documents and analyzer artifacts below `architecture/`.
Do not launch agents, read pipeline logs or source checkouts, edit generated
architecture, or treat a missing legacy coverage sidecar as proof of a missing
behavior.

## Acceptance

- A deterministic audit discovers valid component document/analyzer pairs and
  records malformed or excluded inputs.
- The report separates legacy telemetry availability from nominated surfaces
  and analyzer behavioral-evidence capability.
- Aggregates cover platform, role, priority, and surface ID, with a stable
  representative set spanning available operator, service, and manifest roles.
- Exact observed and precise unresolved behavioral records remain distinct from
  generic candidates.
- JSON and Markdown reports are reproducible and include input fingerprints and
  explicit interpretation limits.
- Coverage enforcement remains warning-only and component-generation workers
  remain disabled.

## Progress

- Added a deterministic read-only scanner, JSON/Markdown renderers, explicit
  output guards, input fingerprints, and fixture regressions.
- Audited 901 canonical component documents and 149 valid document/analyzer
  pairs. The eligible artifacts represent 80 repository identities and nominate
  526 surface occurrences: 314 required and 212 high priority.
- Split the corpus by generation contract using project-owner-provided history:
  654 pre-3.6 documents used the external `architecture-analyzer` with full LLM
  control, 149 documents have valid project `arch-analyzer` pairs, and 98
  3.6-era or rolling documents without stored project analyzer artifacts remain
  unclassified. The legacy cohort is not reported as missing analyzer output.
- Confirmed that all 149 stored analyzers lack `behavioral_evidence` and all 149
  eligible components lack surface-coverage sidecars. The report records those
  conditions as unavailable analyzer and legacy telemetry, not behavioral
  omissions.
- Selected a stable review set with three distinct repository identities for
  each available primary role: operator, service, manifest, and unknown.
- Ranked four follow-ups: refresh stored behavioral evidence, narrow runtime
  FIPS applicability, improve unknown-role classification, and define the
  legacy sidecar adoption boundary.

## Validation

- `uv run pytest -q tests/test_architecture_surface_rollout_audit.py tests/test_architecture_surface_coverage.py tests/test_architecture_surface_fixtures.py tests/test_architecture_surface_canary.py` — 65 passed.
- `uv run ruff check evaluations/architecture-surface-coverage tests/test_architecture_surface_rollout_audit.py` — passed.
- A second audit run matched both durable report files byte for byte.
- `git diff --check` — passed.
