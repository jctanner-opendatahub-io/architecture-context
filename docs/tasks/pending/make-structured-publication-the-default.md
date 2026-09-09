# Task: Adopt the structured component layout

Status: pending — **active**.
Decision: [ADR-0027](../../decisions/ADR-0027-agent-loop-generation-with-structured-layout.md).
Revised 2026-09-09 after tracing the route's blockers and confirming the objective.

## Goal

Move normal component generation onto the four-file layout:

```text
analyzer.json
synthesis.json
document.json
component.md
```

Generation behavior does not change. Components are still produced by the
analyzer-preseeded agent route with repository read access. What changes is the
agent's output contract and what the parent publishes.

Everything downstream of the producer is built and independently accepted:
publication, atomic replacement and recovery, schemas, document assembly, the
renderer, mixed legacy/structured consumers, `arch-query`, indexes, diagrams,
lint, and embedded packaging.

## First action

Run Step 0 of the plan's
[adoption path](../../plans/structured-component-assembly-consolidated.md#adoption-path-adr-0027):
one component, one model call, existing code, a three-line input file. Confirm
the four files and rendered Markdown match intent before any producer work.
Slices 1 and 2 there are the sized implementation steps.

## Scope

- Change the `repo-to-architecture-summary` skill's final output from a Markdown
  candidate to JSON valid against the accepted response schema.
- Validate the agent's JSON before acceptance; add a bounded repair path for
  malformed output and an explicit failure state when repair does not succeed.
- Route accepted output through the existing publication path so a successful
  generation writes the four artifacts as one validated package.
- Preserve the static-analysis phase and analyzer artifacts as internal inputs.
- Record producing conditions honestly in `synthesis.json`: agent route, model
  identity, settings, and observed read/search telemetry where available.
- Keep the tool-free bounded route, its evidence bundle, and `--structured-inputs`
  available behind their existing flags. Do not delete them; do not default to them.
- Provide an explicit legacy-generation option producing today's flat Markdown
  output, byte-preserving for existing callers.
- Update CLI help, README, AGENT_USAGE, and migration notes.
- Add tests for schema-valid output, malformed output and repair, failed
  generation, publication and recovery, mixed legacy/structured directories, and
  the explicit legacy override.

## Open questions

The nomination and follow-up-scope questions are moot under ADR-0027. Remaining:

- **Reuse selection.** Does the default route auto-resolve a predecessor from the
  platform graph via `resolve_predecessor`, or stay explicitly nominated?
- **Flag surface.** Is `--structured-synthesis` retained as a deprecated no-op or
  removed, and what is the legacy switch called given that
  `--no-evidence-gated-merge` already uses "legacy generation" in its help? The
  current `--structured-synthesis` help is stale: the route does publish
  (`publish_private_run` in `run_pipeline_seam`).
- **Command scope.** Does the change apply to `generate-architecture` only, or
  also to `pipeline` and `all` (`lib/phases/orchestration.py:188`, `:392`)?

## Non-goals and boundaries

- Do not run a live model or pipeline generation as part of planning or review
  without separate authorization.
- Do not claim that making the file format the default proves model quality, cost
  savings, or safe rollout.
- Do not silently convert old generated files by renaming or copying them into
  the new four-file package. Conversion must retain provenance and use the
  existing explicit legacy-conversion rules.
- Do not invent missing source observations, model response identity, producing
  settings, or reuse eligibility. Missing observations must produce a clear
  conservative miss or unresolved state.
- Do not enable coverage enforcement or component-generation workers.

## Requirements and acceptance checks

- **Default selection:** running `generate-architecture` with no extra flags
  produces a validated four-file package for a component with valid analyzer
  output, using the existing agent route.
- **No manual input file:** the command succeeds without `--structured-inputs`,
  which is not consulted on the default route.
- **Producer output:** agent output that is not schema-valid is repaired within
  the bounded limit or fails explicitly; malformed output is never accepted.
- **Honest provenance:** `synthesis.json` records the agent route, model identity,
  settings, and observed telemetry; absent telemetry is recorded as unavailable
  and never invented.
- **Legacy escape hatch:** the legacy route is available only through an explicit
  documented option and remains byte-preserving for existing callers.
- **No Markdown input:** no prior Markdown architecture file is parsed or merged
  to construct a component.
- **Publication:** successful generation creates the four related artifacts as one
  validated package; partial or failed replacement cannot leave a falsely
  complete package.
- **Reuse:** a verified eligible predecessor makes zero generation calls; missing
  producer, search, read, or response evidence remains a conservative miss.
- **Failure behavior:** ordinary component failures remain actionable and do not
  incorrectly replace a prior accepted package; actual rate limits stop the run
  and retain durable diagnostics without fallback.
- **Compatibility:** arch-query JSON queries, complete Markdown consumers,
  indexes, diagrams, mixed legacy directories, and rollback behavior continue to
  work.
- **Verification:** focused tests, full relevant Python and Go checks, lint,
  normal and embedded builds, and a fresh independent review pass against a
  frozen final input manifest.
- **Documentation:** a user following the README can run the normal command
  without knowing the structured input schema and can find the explicit legacy
  option when needed.

## Review and rollout

Requires a fresh independent review after implementation, inspecting the changed
producer output contract, validation and repair, default route selection, legacy
override, publication and recovery boundaries, and all affected consumers.

The implementation may be accepted as an offline code and packaging change
without authorizing a live model trial. A separate live-canary task must still
measure quality, calls, latency, tokens, cost, unsupported claims and follow-up
frequency before any adoption or rollout decision.

## Related records

- [Structured assembly completion](../../notes/structured-component-assembly-completion.md)
- [Consolidated structured assembly plan](../../plans/structured-component-assembly-consolidated.md)
- [Live structured-component canary](evaluate-structured-component-live-canary.md)
- [Publication migration ADR](../../decisions/ADR-0025-structured-component-publication-migration.md)
- [Rejected input-fingerprint reuse ADR](../../decisions/ADR-0026-deterministic-input-fingerprint-reuse.md)
- [Agent-loop generation ADR](../../decisions/ADR-0027-agent-loop-generation-with-structured-layout.md)
