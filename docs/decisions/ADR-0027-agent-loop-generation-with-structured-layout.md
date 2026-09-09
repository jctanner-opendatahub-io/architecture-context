# ADR-0027: Generate Through the Existing Agent Loop, Publish the Structured Layout

## Status

Accepted 2026-09-09; implementation pending. Amends the synthesis protocol in
[ADR-0025](ADR-0025-structured-component-publication-migration.md). Publication,
document assembly, schemas, renderer, and consumers are unchanged.

## Context

The objective is adopting the four-file component layout. The structured route
built for that objective also replaced how generation works: it is tool-free by
construction. The adapter protocol requires `tool_free_enforced`, `invoke` raises
`AdapterCapabilityError` when an adapter cannot guarantee a tool-free single
response (`lib/structured_component_synthesis.py:232`), and the Codex adapter
cancels on tool activity (`:270`). The model never reads the repository. It
receives a parent-assembled bundle and may only ask for more source through
bounded `evidence_requests` drawn from a parent allowlist.

That constraint was not the goal; it was a means to make evidence provenance
checkable. It also blocks the layout, because it requires a deterministic input
builder that nominates source ranges on the model's behalf, and no such builder
exists or has an agreed evidence source.

The user's expectation, and the behavior that has actually produced the existing
corpus, is the analyzer-preseeded agent route with ordinary repository read
access.

## Decision

Separate the two changes that were bundled together. Adopt the new layout; keep
the existing generation behavior.

1. Component generation continues on the current analyzer-preseeded agent route
   with repository read access. Tool-free bounded synthesis is not used for
   normal generation.
2. The agent's final output becomes structured JSON validated against the
   accepted response schema instead of a Markdown candidate. No Markdown is
   parsed or merged to construct a component; SC-01 is preserved by changing the
   producer's output contract rather than by constraining its reads.
3. The parent publishes `analyzer.json`, `synthesis.json`, `document.json`, and
   the rendered `<component>.md` through the already-implemented and reviewed
   publication path, with its existing atomic replacement, recovery, and
   cross-file hash binding.
4. The tool-free adapters, parent-built evidence bundle, nominations,
   `allowed_followup_paths`, `evidence_requests`, and `--structured-inputs`
   remain in the tree and remain available. They are not the default route and
   are not deleted.
5. Reuse eligibility rests on harness read and search telemetry rather than
   parent-chosen evidence. Incomplete telemetry remains an explicit conservative
   miss; SC-25 is unchanged.

## What this gives up

The parent no longer owns every byte the model sees, so evidence provenance is
established by observing the agent rather than by constraining it. That is a
weaker property than the one ADR-0025 assumed, and it is the deliberate price of
keeping generation behavior that is known to work.

Bounded single-call synthesis, its follow-up protocol, and its repair path are
sidelined for normal generation. A significant part of the synthesis module
becomes unused by the default route. Retaining it is not evidence that it is
exercised.

No quality comparison exists between the two producers. This decision is made on
intent and known-working behavior, not measurement.

## Consequences

- The layout migration no longer depends on a deterministic input builder, which
  was the only remaining blocker. The nomination and follow-up-scope questions
  are moot for the default route.
- The `repo-to-architecture-summary` skill's output contract changes from
  Markdown to schema-valid JSON. Malformed output needs a bounded repair path.
- The existing corpus remains legacy-format and is not converted in bulk;
  mixed-format consumers already handle that.
- The bounded live canary is still required before regenerating a full version,
  now to compare structured-JSON agent output against the existing corpus.
- Reuse becomes effective from the version after the first structured
  generation, and only where telemetry is complete.
