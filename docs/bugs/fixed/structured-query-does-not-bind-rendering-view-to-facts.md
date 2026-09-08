# Structured query adapter does not fully bind rendering_view to accepted facts

Status: fixed. Independently verified by SC-18 review on 2026-09-07.

The new `src/arch-query/internal/documentdata` adapter validates schema, identity,
fact IDs, accounting and proposal provenance, but does not recompute every
`rendering_view` value from accepted facts. Its implementation worker explicitly
reported this limitation. Code inspection confirms that its integrity checks
do not invoke the existing analyzer `internal/structured.Validate` validator.
An internally contradictory document must not become authoritative query data.

Requirements: SC-18, supporting SC-01/05/06/08. No independent gate has accepted
the new query adapter. This is distinct from P4 external publication hash links.

Repair direction: expose a narrow public byte-input validation entry point that
delegates to the analyzer's accepted-document validator and call it from the
query adapter. Preserve one semantic validation implementation, standalone
compiled query behavior, central schemas, and the current publication boundary.
The coordinator will assign the shared interface once the SC-18 worker finishes
its existing bounded handoff; no overlapping edits.

Acceptance: mutate rendering_view while leaving accepted facts unchanged and
require actionable failure with no legacy fallback. Independently test shared
validation against accepted fixtures, typed/provenance tampering and existing
query/parity/embedded checks. This record is based on source inspection and the
worker's disclosure, not a completed adversarial test.

Independent PASS: `20260907-resume/sc18-review-report.md`. The required post-P2-repair
freeze check verified all 276 SC18 inputs unchanged; P2 changed only its six
authorized Python/reuse-note files. Evidence: `sc18-post-p2-repair-freeze-check.json`.
