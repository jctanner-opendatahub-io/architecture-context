# Project Plan

## Current Milestone

Continue the analyzer-assisted track: valid analyzer artifacts default to the
bounded partial (extend-and-improve) route for all readiness classifications
(sufficient, partial, insufficient, unknown); synthesis is not selected for
normal generation; the synthesis migration allowlist is retained for audit
only; legacy is reserved for missing/invalid artifacts or explicit operator
override. External rollout gates remain separate. The next implementation
milestone is the [arch-analyzer optimization follow-up](docs/plans/architecture-context-static-migration.md),
driven by the completed 97-component run.
The analyzer gap evidence and read justification plan is complete; its replay
measurements are recorded in
[docs/notes/architecture-context-static-migration.md](docs/notes/architecture-context-static-migration.md).
The next focused milestone is the
[arch-analyzer evidence quality follow-up](docs/plans/architecture-context-static-migration.md).

## Active Tasks

- [Checkpoint Surface Work and Restore Validation](docs/tasks/current/checkpoint-surface-work-and-restore-validation.md) — in progress; checkpoint first, then baseline repair follows FIPS applicability.
- [Fix Surface FIPS Applicability](docs/tasks/pending/fix-surface-fips-applicability.md) — next code fix after checkpoint.
- [Refresh Surface Analyzer Evidence](docs/tasks/pending/refresh-surface-analyzer-evidence.md) — pending source inputs and scoped regeneration approval.
- [Run Repeated Surface Coverage Live Canary](docs/tasks/pending/run-surface-coverage-live-canary.md) — deferred pending model access and explicit live-run approval.
- [Decide Surface Coverage Rollout](docs/tasks/pending/decide-surface-coverage-rollout.md) — separate enforcement/worker decisions; defaults remain unchanged.
- [Audit Architecture Surface Rollout](docs/tasks/done/audit-architecture-surface-rollout.md) — completed read-only audit; stored artifacts lack the evidence needed for an enforcement decision.
- [Improve Architecture Surface Coverage](docs/tasks/done/improve-architecture-surface-coverage.md) — implemented and independently reviewed; the offline-canary selection remains provisional pending any separate rollout decision.
- [Complete the Architecture Context Static Migration](docs/tasks/done/complete-architecture-context-static-migration.md) — consolidated implementation and iteration history.
- [Replace Markdown Change Records with a JSON Patch Contract](docs/tasks/pending/replace-markdown-change-record-with-json-patch.md) — pending workflow hardening.
- [Resolve External Analyzer-Assisted Rollout Gates](docs/tasks/blocked/resolve-external-analyzer-assisted-rollout-gates.md) — blocked on external and human inputs; not a local implementation blocker.

## Open Bugs

- [Partial Route Component Runtime Remains High](docs/bugs/open/partial-route-component-runtime-remains-high.md)
- [Surface Inventory Nominates Empty FIPS Category](docs/bugs/open/surface-inventory-nominates-empty-fips-category.md)

## Plans

- [Architecture Surface Coverage](docs/plans/architecture-surface-coverage.md)
- [Architecture Context Static Migration](docs/plans/architecture-context-static-migration.md)
- [Architecture Diagram Implementation](docs/plans/000-architecture-diagram-implementation.md)

## Decisions

- [ADR-0001: Architecture Diagram Proposal](docs/decisions/ADR-0001-architecture-diagram-proposal.md)
- [ADR-0002: Skills-First MVP](docs/decisions/ADR-0002-skills-first-mvp.md)
- [ADR-0003: Python Orchestrator Pipeline](docs/decisions/ADR-0003-python-orchestrator.md)
- [ADR-0004: Kustomize Overlay Context Injection](docs/decisions/ADR-0004-kustomize-overlay-context.md)
- [ADR-0005: Architecture Context Overlays](docs/decisions/ADR-0005-architecture-context-overlays.md)
- [ADR-0006: platforms.yaml Configuration](docs/decisions/ADR-0006-platforms-yaml.md)
- [ADR-0007: component-map.json Intermediate Artifact](docs/decisions/ADR-0007-component-map-json.md)
- [ADR-0008: Pure Skill Invocation](docs/decisions/ADR-0008-pure-skill-invocation.md)
- [ADR-0009: Sub-Agent Dispatch](docs/decisions/ADR-0009-sub-agent-dispatch.md)
- [ADR-0010: arch-query Go CLI](docs/decisions/ADR-0010-arch-query-go-cli.md)
- [ADR-0011: rhoai.next Rolling Target](docs/decisions/ADR-0011-rhoai-next-rolling-target.md)
- [ADR-0012: Linting and CI](docs/decisions/ADR-0012-linting-and-ci.md)
- [ADR-0013: Webhook Inventory Phase](docs/decisions/ADR-0013-webhook-inventory-phase.md)
- [ADR-0014: Declarative exclude_files](docs/decisions/ADR-0014-exclude-files.md)
- [ADR-0015: Build Metadata Extraction](docs/decisions/ADR-0015-build-metadata-extraction.md)
- [ADR-0016: Image and Repo Provenance](docs/decisions/ADR-0016-image-and-repo-provenance.md)
- [ADR-0017: Selectable Agent Harness](docs/decisions/ADR-0017-selectable-agent-harness.md)

## Notes

- [Architecture Context Static Migration](docs/notes/architecture-context-static-migration.md)
- [Architecture Diagram Requirements](docs/notes/architecture-diagram-requirements.md)
- [Webhooks feature reference](docs/notes/webhooks.md)
