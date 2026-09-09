# Structured Component Assembly: Consolidated Implementation Plan

## Status, authority, and provenance

Consolidated 2026-09-06. Execution started 2026-09-06; phase-one deterministic
gate and bounded SC-18 adapter independently accepted. Phase-two bounded reuse is independently accepted; bounded synthesis and publication/consumers are independently accepted;
final offline evidence and integration gate independently accepted on 2026-09-09.
The authorized implementation is complete. SC-24 live evaluation and default
adoption remain HOLD under the [separate live task](../tasks/pending/evaluate-structured-component-live-canary.md).
See the [completion record](../notes/structured-component-assembly-completion.md)
for the final verdict, evidence identities and retained nonblocking limits.
This is the authoritative
implementation plan for this effort; it replaces the conflicting design options
in the [original proposal and review history](structured-component-assembly.md).
The original file is preserved unchanged. Its SHA-256 at consolidation is
`65a62e75850cadf9ffefa9c6b6cd6b55b2b1d3e8058142a479d11fe0d1157217`.

This plan incorporates the closed Claude/Codex consensus, the user's requirement
to retain model output for auditing, cross-version component reuse, and explicit
consumer compatibility requirements. The traceability table below records
preserved, superseded, and deferred requirements. Historical reviews explain the
decisions; implementers should follow this consolidated contract.

The objectives are to remove Markdown parsing from component construction and
avoid repeated synthesis when architectural inputs have not changed. Markdown
remains a supported consumer product. Structural correctness does not establish
semantic truth. Existing coverage stays warning-only and component-generation
subagents stay disabled. Live generation and default-route adoption require
separate authorization and evidence.

## Intent and 2026-09-09 amendment (ADR-0027)

The user's intent, restated so every later step can be checked against it:

1. **Adopt the four-file component layout** — `analyzer.json`,
   `synthesis.json`, `document.json`, `<component>.md`. This is the objective.
2. **Generation keeps working the way it does now**: an agent preseeded with
   analyzer output that reads the repository with ordinary tools. The tool-free
   single-call producer built under SC-10 is not what was asked for. It stays
   available as an opt-in variant and is not the default.
3. **Reuse of previous generations** is wanted, is a consequence of (1), and
   becomes possible only from the second version generated on the new layout. It
   is not a precondition and is not pursued through a separate mechanism
   ([ADR-0026](../decisions/ADR-0026-deterministic-input-fingerprint-reuse.md), rejected).
4. **No further multi-day implementation before a one-component intent check**
   shows the layout and rendered Markdown are what the user wants. See
   [Adoption path](#adoption-path-adr-0027).

Phases 1, 2, 4 and 5 stand. SC-10 is superseded on the default route by
[ADR-0027](../decisions/ADR-0027-agent-loop-generation-with-structured-layout.md).
Where the body below describes bounded tool-free synthesis as the default,
ADR-0027 governs.

## Explicit requirements and acceptance checks

These requirements are binding for implementation. Every phase report must name
the requirement IDs it verifies, the test/evidence, and any unfinished IDs.

| ID | Requirement | Acceptance check |
|---|---|---|
| SC-01 | Keep component construction in JSON through accepted assembly; render Markdown from the accepted model. | New-route tests make no candidate-Markdown parse or merge calls. |
| SC-02 | Publish four core artifacts: analyzer JSON, synthesis JSON, document JSON, and existing component Markdown. | Layout tests cover required files, optional diagrams, and explicit legacy/deterministic-only synthesis states. |
| SC-03 | Retain original model proposals independently of disposable logs. | Removing run logs leaves response payloads, hashes, origin, and accepted/rejected proposal mappings available. |
| SC-04 | Use one renderer implementation, extending the analyzer renderer. | Shared renderer reproduces the baseline; any arch-doc wrapper delegates instead of duplicating rendering rules. |
| SC-05 | Preserve every analyzer fact unless an authorized typed change applies. | Fact accounting and renderer tests include resource, non-resource, mixed, and legacy RBAC; unmapped required types fail explicitly. |
| SC-06 | Apply typed patches without duplicate Markdown candidate rows. | Tests cover stable IDs, bundle fingerprints, authority, referential integrity, conflicts, and ambiguous legacy operations. |
| SC-07 | Render headings, parent sections, tables, and citations from schemas. | FIPS has a fixed Security parent; current conditional sections remain supported; invalid structures fail with durable diagnostics. |
| SC-08 | Preserve canonical aliases, repository identity, version scope, and explicit uncertainty. | Praxis fixtures retain prefixes and remain included without claiming current integration. |
| SC-09 | Preserve attributed human corrections and distinguish implementation, support, and planned behavior. | Overlay applicability/conflict tests retain provenance and never promote roadmap intent to observed implementation. |
| SC-10 | ~~Default to~~ Offer one structured synthesis call over an orchestrator-built evidence bundle, with bounded evidence follow-up. **Superseded as the default by ADR-0027; retained opt-in.** | Tests verify one-call completion, fixed follow-up/repair limits, explicit unresolved outcomes, and no open-ended tool loop on the new route. |
| SC-11 | Implement whole-component cross-version reuse early. | Identical relevant inputs and verified equal semantic/evidence inputs across new commits make zero synthesis calls. |
| SC-12 | Select a predecessor explicitly and validate reuse eligibility. | `reuse_from` tests cover missing/cyclic/self references, aliases, wrong repositories, incompatible or rejected snapshots, and explicit refresh overrides. |
| SC-13 | Fingerprint every semantic input supplied to synthesis. | Exclusions have documented reasons and invalidation tests; versions, permissions, conditions, and meaningful ordering remain significant. |
| SC-14 | Verify source and search dependencies independently of model assertions. | Tests cover observed-read reconciliation, file hashes, actual search scopes/options, dirty content with unchanged HEAD, and incomplete telemetry causing a reuse miss. |
| SC-15 | Preserve reuse provenance and revalidate accepted output. | Reuse retains original response identity, records target and comparison hashes, and cannot bypass current patch/schema checks. |
| SC-16 | Keep platform synthesis separate from component reuse. | A platform-only integration change leaves unchanged component synthesis reusable; real component input changes invalidate normally. |
| SC-17 | Publish files atomically and detect/recover inconsistent derivatives. | Crash/failure tests detect mismatched JSON inputs and stale Markdown; repair rerenders accepted models without model calls. |
| SC-18 | arch-query must support the new files and folder structure. | Queries consume accepted document.json directly, support mixed legacy/new corpora, preserve existing query/CLI behavior and citations, and never treat metadata or rejected synthesis as components/facts. |
| SC-19 | Existing RFE/STRAT Markdown consumers must continue working. | Golden/contract checks preserve flat component paths, PLATFORM.md/INDEX.md links, section/table contracts, source references, and prefixed names. |
| SC-20 | Index, platform aggregation, and diagram generation must support the accepted model and layout. | Integration tests cover targeted/full runs, legacy fallbacks, relative links, stale derivatives, and current/planned relationships. |
| SC-21 | Audits, collectors, linters, and packaged/embedded consumers must recognize metadata correctly. | Enumeration tests exclude index/JSON/run files from component counts and diagram jobs; packaging retains required accepted artifacts. |
| SC-22 | Preserve coverage knowledge without publishing detailed evaluation history. | Applicable unresolved surfaces travel in document.json; missing legacy telemetry is unavailable, not evidence of omissions; warning-only policy stays intact. |
| SC-23 | Preserve historical evidence and support explicit migration/rollback. | Saved canary hashes remain unchanged; mixed-schema and rollback tests avoid silent field loss or bulk historical rewrites. |
| SC-24 | Measure cost and quality before adoption, with independent review. | Report candidate versus verified reuse, calls/tokens/latency, preservation, unsupported claims, follow-up frequency, and a reviewed adoption/hold decision. |
| SC-25 | Snapshots are reuse-eligible only when the producing harness recorded complete read and search observations. | Codex-produced snapshots miss until the open `rg` search-classification bug is fixed and Codex telemetry records resolved search roots, patterns, and options; tests cover an unclassified search causing an explicit miss. |

## Published layout and artifact ownership

```text
architecture/<version>/
├── INDEX.md
├── PLATFORM.md
├── component-map.json
├── praxis-policy.md
└── praxis-policy/
    ├── analyzer.json
    ├── synthesis.json
    ├── document.json
    └── diagrams/             # Optional derived assets
        ├── component.mmd
        └── component.svg
```

`analyzer.json` retains deterministic extraction and provenance. It is immutable
within an accepted snapshot. `document.json` is the accepted normalized model
with facts, synthesis, evidence, uncertainty, applicable corrections, producer
versions, input/output hashes, and proposal dispositions. Markdown derives from
that model. Execution timing belongs in run records, not reproducible content.

`synthesis.json` retains the original response payloads within a versioned
orchestrator envelope. It includes requested/reported model identity where
available, settings, exact input-bundle identity, and response hashes. Keep exact
response text where necessary to distinguish raw output from parsed JSON. Do
not rewrite model proposals to match accepted output. Accepted and rejected
proposals map to stable IDs or JSON pointers with reasons in `document.json`.

When bounded follow-ups or repairs contribute to a snapshot, preserve their
responses and order in synthesis.json, with input fingerprints and separately
attributed request-resolution outcomes. A reused snapshot carries the originating
synthesis artifact unchanged; the new reuse record belongs in document.json.
Missing historical responses and deterministic-only generation are explicit
states, never fabricated model output. Wholly failed runs cannot replace a
previous accepted snapshot. Normal repository history retains replaced snapshots.

Central versioned schemas live under `schemas/`. No separate published manifest,
patch, per-section synthesis, coverage, read-log, or validation file is required;
necessary accepted provenance resides in the core artifacts. Optional diagrams
carry the accepted document hash, renderer/generator identity, and availability
state in derivative metadata. Diagrams have no programmatic consumers; only
humans read them, so relocating them under the component directory needs no
compatibility shim beyond updating `AGENT_USAGE.md` and the diagram phase's
output path. Diagram failure does not invalidate accepted component facts.

## Run artifacts and synthesis protocol

```text
logs/pipeline/<run-id>/generate-architecture/<component>/
├── input-manifest.json
├── evidence-bundle.json
├── attempts/
│   └── 01/
│       ├── response.json
│       └── validation.json
├── source-reads.json
├── coverage.json
├── insights.json
├── validation.json
└── run.json
```

The orchestrator supplies analyzer facts, applicable corrections, schemas, and
bounded source evidence nominated by the analyzer. The model returns one JSON
response containing named synthesis sections, proposed changes, limitations,
and optional evidence requests. The orchestrator writes files. A model does not
need file-writing calls for separate sections. Splitting response fields into
additional run files is optional and must not create extra model invocations.

Use fixed configurable limits for evidence follow-ups, response repairs, and
total calls. Validate requested paths/ranges and scope, fetch justified evidence,
then resubmit. Exhausted evidence budgets produce unresolved questions; invalid
required structure produces failure. No silent fallback to incomplete content
or legacy Markdown. An unrestricted iterative discovery agent is retained only
for the explicit legacy route. Resolve SDK/provider authentication compatibility
without assuming that the new response contract requires a new credential type.

The parent records evidence it actually supplies, and retains harness observations
where tools are used. Observations and agent justifications are distinct. Full
transcripts, tool output, detailed evaluation history, and unrelated failed runs
remain logs. Essential response/provenance data survives independently in the
accepted snapshot; hashes establish identity, not availability of source inputs.

## Typed assembly and rendering

Normalize analyzer JSON directly into versioned facts with deterministic IDs and
source mappings. Resource permissions and nonResourceURLs are distinct typed
values; mixed rules retain both. Never invent missing legacy URL values.

Define the new patch contract around a bundle fingerprint, fact IDs, typed values,
authority, evidence, and reasons. Missing proposals fail where required; an empty
operations array is valid. No per-operation stale-target precondition system is
required. Validate the proposal against the exact bound input, detect conflicting
operations, and preserve the unchanged analyzer facts. Apply authorized changes
and overlays with explicit dispositions in the accepted model.

All analyzer-owned facts participate in accounting, including types unfamiliar
to the renderer. Unsupported required schemas/types fail explicitly. Validate
source ranges, identity, evidence scope, and references before assembly. Old
ambiguous v1 patches remain conservative errors until explicitly convertible.

A section registry owns headings and hierarchy, including FIPS under Security
and supported conditional sections such as Multi-Tenancy, AIPCC Ecosystems Use,
Sub-Component Details, and Deployment Manifests. Prose may use constrained inline
formatting and lists; arbitrary structural Markdown/HTML cannot bypass the
schema. Flows and security tables use typed entries with evidence and unknowns.
Normalization and rendering must preserve all valid baseline facts. Byte parity
is the initial target, with explicit expected differences for intentional fixes.

Extend the analyzer's renderer as the sole rendering implementation. arch-doc
may remain a compatibility wrapper or be retired after callers migrate; this is
an interface choice, not permission for a second renderer. Rendering needs only
the accepted document and renderer configuration, with no source reads or model
calls. Schema correctness never substitutes for semantic claim review.

## Cross-version component reuse

Whole-component reuse is phase 2, directly after deterministic rendering parity.
`platforms.yaml` selects the predecessor through `reuse_from`. Resolve immutable
snapshot identity and repository/canonical component identity; directory naming
alone is insufficient. Commit/tree equality is a cheap comparison path, but
relevant configuration, overlays, contracts, and acceptance status still matter.

Maintain two fingerprints: exact input identity for audit, and a versioned semantic
fingerprint for reuse. The reuse eligibility record includes predecessor identity,
canonical repository/component identity, normalized analyzer inputs, supporting
file content hashes, searched-scope identities/options, applicable component
configuration/overlays, synthesis contract/settings, and analyzer/normalization
compatibility. `synthesis.json` is excluded from the input key; hash it separately
for integrity. Renderer versions affect derivatives, not synthesis eligibility.

Include every semantic analyzer field supplied to synthesis. Exclude volatile
timestamps, commit labels, checkout paths, and schema-version labels from the
semantic payload, while retaining producer/schema compatibility separately.
Separate scan statistics from facts in analyzer output, with documented exclusion
rules and tests. Keep dependency versions, conditions, permissions, and meaningful
ordering. Do not blanket-exclude synthesis evidence, cross-references, coverage
findings, or gap questions. `recent_changes` is refreshed deterministically and
excluded from the reusable synthesis input bundle; if future synthesis consumes
it, it must enter the key. Target release labels alone are not semantic changes.

Compatibility initially requires exact producer and normalization versions.
Explicitly reviewed compatible-version ranges may follow later; normalization
alone does not make analyzer upgrades cache hits. Record the actual producer
build, including uncommitted source identity where relevant, rather than relying
on a version string that cannot distinguish changed extractors.

Use independently recorded observed/supplied reads, reconciled with justifications,
to form evidence dependencies. Hash whole supporting files initially. Retain
resolved search roots, patterns/options, and directory tree hashes for negative
findings on a clean tracked snapshot. Account for untracked/generated/external
inputs separately or declare reuse unavailable. Verify unchanged HEAD and actual
working-tree inputs across the run; HEAD equality alone is insufficient. Missing
or incomplete dependency records are explicit misses, including any snapshot
whose harness could not classify every search it ran (SC-25; the Claude guard
already resolves search roots, Codex telemetry does not yet). Positive fact matches
alone do not establish verified synthesis reuse.

| Situation | Required action |
|---|---|
| Equal source and all relevant inputs | Reuse with zero synthesis calls |
| New commits, equal semantic facts and verified supporting dependencies | Reuse with zero synthesis calls and record comparison evidence |
| Changed semantic facts or supporting files/search inputs | Reconsider whole-component synthesis |
| Missing dependencies, invalid prior output, incompatible contract, or explicit regeneration | Record miss reason and use normal bounded synthesis |

Platform synthesis is outside this decision. Praxis integration changes update
platform explanations and index integration metadata separately; changes to the
component's own configuration/facts, including internal_dependencies, invalidate
normally. Keep current and planned relationships distinct and attributed.

No citation relocation in the first implementation: changed supporting files
miss even if a cited excerpt remains identical. Later range/symbol-aware reuse
requires verified surrounding dependencies. Reused responses remain original;
document.json records prior/target snapshots, reasons, comparison hashes, and
current provenance. Revalidate patch/fact references and current acceptance rules
before publishing reused content. Renderer-only changes rerender with no model
call. Section-level invalidation and broad dependency analysis are deferred.

## Publication and consumers

Validate staged inputs before updating published files. document.json is the
accepted authority and references analyzer/synthesis hashes. Publish each file
atomically, serialize concurrent writes per component, retain recoverable prior
inputs until publication completes, and reject mismatched snapshots. Markdown
records the input document hash and renderer identity; stale Markdown is repaired
by rerendering. Multi-file atomic visibility is not promised. Repository publication
must verify matching inputs and derivatives before exposing a completed snapshot.
Tests must cover interruption before/after each replacement and deterministic
recovery without another model call. This is a small local publication protocol,
not a separate manifest transaction subsystem.

arch-query must load document.json through a schema-aware adapter when a valid
accepted model exists, and use the legacy Markdown reader for explicitly legacy
components. Preserve current query results, component filtering, provenance,
section access, and Markdown export where supported. Unsupported/mismatched new
models produce actionable errors rather than silently mixing old Markdown with
new JSON. Test JSON queries without component Markdown, parity against equivalent
Markdown fixtures, mixed version directories, non-resource RBAC, prefixes, and
existing embedded/packaged data paths. This verifies compatibility; it does not
repeat the flat-file versus arch-query synthesis benchmark.

### arch-query adapter scope (SC-18)

Sized against the current code so the work is planned, not assumed.

Current shape: every arch-query command consumes one struct,
`types.ComponentDoc`, and the only place that struct is built is
`LoadVersion` in `internal/loader/loader.go`. That loader already has two input
paths, the Markdown parser (`internal/markdown`, ~400 lines) and an analyzer
JSON mapper (`internal/jsondata`, ~300 lines, no tests), merged with
"supplement if empty" rules. Selection is by file existence with parse errors
silently skipped, which is exactly the ambiguous precedence this plan forbids.
Only `grep` reads raw Markdown section text; every other command reads typed
fields.

Work items:

1. A `document.json` mapper into `ComponentDoc`, modeled on the analyzer JSON
   mapper, covering every field the Markdown parser populates plus typed RBAC
   (resource and non-resource) and proposal dispositions where a command needs
   them. Expected size is comparable to the existing mapper.
2. Loader selection by schema identity: when a component directory holds a
   valid `document.json` of a supported schema version, it is authoritative
   for that component and the sibling Markdown is not parsed for facts.
   Components without it use the legacy Markdown plus analyzer JSON path.
   Invalid or unsupported `document.json` is a reported error for that
   component, never a silent fallback to Markdown.
3. `grep` and `--output raw` keep reading the rendered Markdown, since it is
   a published derivative of the accepted model; no JSON text projection is
   needed.
4. Parity test: load the same component through the Markdown path and the
   `document.json` path and assert identical `ComponentDoc` values apart from
   raw sections. Add the missing unit tests for the existing JSON mapper at the
   same time.
5. Mixed-corpus test: one version directory with legacy and new components,
   component counts and `versions` output unchanged, metadata directories not
   counted as components.
6. Embedded build: confirm the `_embedded/architecture` copy includes
   `document.json` and `analyzer.json` and excludes run artifacts.

Isolation and scheduling: commands are untouched; the change is confined to
`internal/loader`, a new mapper package, and tests. It depends only on the
`document.json` schema from phase 1, so run it as a parallel track starting
after phase 1 rather than serializing it inside phase 4. Phase 4 then only
integrates and verifies it. Report it as its own line item in phase reports.

RFE/STRAT consumers keep flat component Markdown and platform/index paths.
Version indexes and platform aggregation prefer accepted models with explicit
legacy compatibility. Index generation remains deterministic after platform
architecture and before diagrams. Diagrams consume accepted facts/relationships;
audits, linters, collection and packaging exclude metadata and run artifacts from
component enumeration. No platform-wide JSON redesign or mandatory downstream
skill migration is required to finish this component change.

Legacy `.analyzer`/`.generation` layouts and patch/Markdown readers remain explicit
compatibility paths during migration. Select using schema/route identity, not
ambiguous file-existence precedence. Do not bulk-rewrite historical versions or
manufacture absent provenance. Define compatibility retirement and default-route
rollback criteria before rollout, preserving the recent promotion repairs until
their replacement guarantees are verified.

## Implementation phases and gates

### Phase 1: deterministic model and rendering parity

Inventory facts, section ownership, and consumers; define just the schemas and
normalization required for an analyzer-to-document-to-Markdown slice. Extend the
existing renderer and establish parity with the baseline before agent/publication
work. Independently review typed identity and preservation fixtures, including
all RBAC variants and conditional sections. Covers SC-01, SC-04 through SC-09.

Gate: deterministic positive/negative tests pass; intentional differences are
recorded; no agent invocation or new publication protocol is needed for this slice.

### Phase 2: whole-component reuse and verified dependency records

Implement explicit predecessors, semantic keys, exact compatibility, evidence
hashing, and hit/miss decisions using accepted structured fixtures. Persist enough
audit data for reuse and collect missing read/search dependencies prospectively.
Existing snapshots lacking trustworthy dependencies miss; do not backfill them
from guesses. Covers SC-11 through SC-16 and SC-25, and supports SC-03.

Gate: tests prove zero-call reuse across unchanged inputs and irrelevant commits,
and misses for changed evidence, search scope, overlays/config, incompatible
versions, invalid prior output, or incomplete telemetry. Include unchanged-HEAD
dirty-worktree, platform-only integration, and unclassified-search cases.

### Phase 3: bounded structured synthesis and typed patch assembly

Wire the default one-response contract behind an opt-in route, build evidence
bundles in the parent, enforce total follow-up/repair limits, and retain response
envelopes. Protect original inputs and distinguish observations, justifications,
and model claims. Exercise both harness adapters through tests. Covers SC-03,
SC-06, SC-07, SC-10, SC-14, SC-15, SC-22.

Gate: successful, unresolved, malformed, and exhausted-budget cases produce
correct artifacts/diagnostics. No implicit legacy fallback, extra per-section
agent, or live model run is required to verify the contract.

Delivered and accepted as an opt-in route. Under ADR-0027 it is not the default
producer; the default producer is the existing agent loop emitting the same
response contract (see Adoption path).

### Phase 4: four-file publication and consumer integration

Implement hash-linked artifacts, per-file atomic publication, stale derivative
detection/recovery, and integrate the arch-query reader delivered by the
parallel SC-18 track (started after phase 1). Update index/platform/diagram
inputs, collection, lint/audits, packaging, and explicit mixed-format fallbacks.
Record the migration ADR before default adoption. Covers SC-02, SC-08, SC-09,
SC-17 through SC-23.

Gate: all consumer requirements are demonstrated, including arch-query queries
against new JSON and mixed corpora; audit survives log removal; crash recovery
works. Snapshot failures and legacy errors remain actionable.

### Phase 5: independent review and scoped adoption evidence

Run appropriate full test/lint gates and independent review. Replay saved canary
fixtures offline through explicit test-only conversions, preserving original
evidence hashes and rejected verdicts. Malformed legacy FIPS placement remains
an explicit conversion error. Conversion does not prove model schema compliance.

Reproduce the reuse comparison with a recorded analyzer build and preserve the
pre-commit baseline. With separate live-run authorization and model/cost bounds,
evaluate rhods-operator plus representative service, manifest, and prefixed
non-integrated components. Measure SC-24, verify all requirement IDs, and record
adopt/hold plus rollback. Enforcement and workers are separate decisions.

## Adoption path (ADR-0027)

### Step 0 — intent check with no new code

About one hour, one model call, requires live authorization. Pick one component
whose analyzer payload is committed; all 149 currently pass the route's input
validation (`validate_legacy_conversion_input`, checked 2026-09-09). Write:

```json
{"schema_version": "1.0.0", "instructions": "", "components": {"<component>": {}}}
```

Run `generate-architecture --platform <version> --component <component>
--structured-synthesis --structured-inputs <file>`. On existing code this
exercises bundle → tool-free call → validation → assembly → four-file publication
→ rendered Markdown → `arch-query`. Inspect the four files, the Markdown, and a
query. Producer quality is *not* the question — with no nominations the model
sees analyzer facts only. The question is whether the layout and rendering are
what the user wants.

Stop rule: if the layout or rendering is wrong, fix that first. Do not start
producer work.

### Slice 1 — agent-loop producer, four-file output

Not a one-to-two-hour change. The Python is small in lines but sits on the
adapter and provenance boundary the seam was built to defend, and review must
inspect it. Expect a focused day for the glue and tests; the skill rewrite is
separate and may be hand-written by the user.

- Add an agent-loop adapter that runs the existing harness (`run_agent`, whose
  telemetry collector already records reads and searches) with repository read
  access and returns the final response JSON. Permit `tool_free_enforced=False`
  for it; the only hard gate is `CallbackStructuredAdapter.invoke`.
- When `--structured-inputs` is absent, use empty per-component records. No
  input builder.
- Make this the default route. Keep tool-free opt-in. Keep an explicit legacy
  flat-Markdown option, byte-preserving.
- Reuse eligibility is recorded as unavailable on this slice (model context
  incomplete); the four files still publish. This is honest, not a failure.
- Skill: emit the response JSON — `sections`, `typed_patches`, `limitations`,
  empty `evidence_requests` — instead of editing `candidate.md`.

Gate: one component regenerated end to end on the default command with no extra
flags; four files validate; `arch-query` reads them; independent review of the
adapter boundary and the provenance record.

#### Hand-implementation notes for Slice 1

Line numbers are as of 2026-09-09. Python first, all in
`lib/structured_component_synthesis.py` unless noted.

1. **Adapter.** `authenticated_harness_adapter` (`:414`) builds a `call`
   closure that invokes `run_agent` at `:467` with `tool_free=True,
   max_turns=1, enable_skills=False`. Add an agent-loop variant (a mode
   argument or sibling factory) with `tool_free=False`, a sane `max_turns` cap
   or `None`, `enable_skills=True`, and keep `response_schema=dict(_schema)`.
   With tools enabled, `run_agent` passes that schema as
   `output_format=json_schema` (`lib/agent_runner.py:940`), so the final
   `raw_response` is schema-enforced JSON and the existing extraction at `:497`
   still works. Construct it with `tool_free_enforced=False,
   context_complete=False, unobserved_context=("agent-tool-use",)` and set
   `implicit_context["tool_policy"]` to describe the real tool set.
2. **Guard.** `CallbackStructuredAdapter.invoke` (`:232`) raises whenever
   `tool_free_enforced` is False. Remove that raise for the agent-loop adapter.
3. **CLI identity.** `run_agent` resolves `claude_cli_identity` only under
   `tool_free` (`lib/agent_runner.py:890`), and the closure requires it
   (`:502`). Make the resolution unconditional.
4. **Checkout access.** `call` receives no request object. Put the absolute
   checkout path into the prompt instructions where the seam builds the request
   (`:3172`, `instructions=`). The temporary `cwd` is fine; tools read absolute
   paths. Pass no `agent_policy`, so `_AgentExecutionGuard` defaults to the
   unrestricted legacy tool set.
5. **Default inputs.** `_load_pipeline_inputs` (`:3013`) raises on `None`.
   Return `{"schema_version": "1.0.0", "instructions": "", "components": {}}`
   instead, and at `:3134` treat a missing component record as `{}`.
6. **Route selection.** `lib/phases/architecture.py:202` enters the seam only
   with `--structured-synthesis`. Flip the default there; add an explicit
   `--legacy-generation` opt-out; fix the stale flag help in
   `_add_structured_synthesis_options` (`lib/cli.py:136`), which still says the
   route does not publish.
7. **Prompt text.** `PARENT_RESPONSE_INSTRUCTIONS` (`:78`) says "Do not invoke
   tools." Use a variant for the agent-loop prompt.
8. **Section acceptance — read this before judging output.** Model sections
   are proposals with no authority. `_select_sections` (`:1265`) accepts a
   section only when a trusted `section_policy` says `accept`; with no policy,
   every model section is recorded as rejected and the document carries analyzer
   facts only. For a first real run, either supply a `section_policy` through
   `--structured-inputs` or add a parent default that accepts model sections you
   are willing to trust. Without this, the rendered Markdown will look like the
   analyzer baseline and that is expected, not a bug.
9. **Reuse.** Leave it. With `context_complete=False` the seam forces refresh
   (`:1637`) and records eligibility unavailable. That is Slice 2.
10. **Tests.** Existing tests assert the tool-free guard and single-turn
    behavior; expect a handful in `tests/test_structured_component_synthesis.py`
    to need updating rather than the code being wrong.

Skill — `.claude/skills/repo-to-architecture-summary/SKILL.md`:

- The prompt now arrives as the canonical JSON request (`evidence_bundle`,
  `response_schema`, `instructions` with the checkout path). Keep the partial
  route's reading discipline (`SKILL.md:68`); retire the candidate-Markdown and
  patch-output contract (`SKILL.md:208-291`).
- The final answer is one JSON object: `schema_version` `"1.0.0"`,
  `response_id`, `input_bundle_identity` copied verbatim from
  `evidence_bundle.bundle_identity`, `completion_status` `"complete"`,
  `sections`, `typed_patches`, `limitations`, and `evidence_requests: []`.
- `sections[]`: `id` from the fixed enum (`aipcc-ecosystems-use`,
  `sub-component-details`, `deployment-manifests`, `security.fips-compliance`,
  `security.build-hermeticity`, `multi-tenancy`), `status`
  (`documented|unresolved|not-applicable`), `blocks`, and `evidence[]` entries
  of `path` plus `revision` (the analyzer `commit_sha`), optionally
  `start_line`/`end_line`.
- `typed_patches[]`: start with `[]`. Sections alone yield a valid document.
  Add fact patches (`patch_id`, `bundle_fingerprint`, `operations[]` with
  `operation_id`, `action`, `fact_type`, target or key/value, `evidence`,
  `reason`) only after the sections path works end to end.
- `limitations[]`: `code`, `detail`, optional `section_id` — say what could
  not be verified rather than omitting it.

Verify:

```bash
uv run main.py generate-architecture --platform rhoai-3.6-ea.2 \
  --component rhods-operator --force --model opus
ls architecture/rhoai-3.6-ea.2/rhods-operator/      # analyzer.json synthesis.json document.json
head architecture/rhoai-3.6-ea.2/rhods-operator.md  # marker binds document hash
make build && make lint
```

Then run any `arch-query` command against `rhoai-3.6-ea.2` and confirm the
component loads from `document.json`.

### Slice 2 — reuse from telemetry

Separate, after Slice 1 is accepted. Feed harness read and search observations
(`dependency_record_from_telemetry`) into the run record so default-route runs
can be reuse-eligible. Codex stays a miss until the `rg` classification bug is
fixed (SC-25). Reuse then becomes effective from the version after the first
structured generation.

## Evidence and cost reporting

The original review counted 84 runs, 101 restored rows, and approximately 34
mean turns. Different reported token totals covered different routes/models;
include fresh, cache-creation, and cache-read usage in future cost reports.
Aggregate cached tokens do not directly predict single-call savings.

The [reuse measurement artifacts](../../evaluations/component-reuse-fingerprint/)
report 92 paired repositories: 11 identical commits, 33 semantic matches, 38
after scan-count normalization, and 40 after dropping dependency versions (not
recommended). Re-including six contested evidence fields retained 38 matches;
including recent_changes reduced them to 11. These are reported candidate rates,
not independently established safe-reuse rates. The original analyzer was built
from commit `39209078` plus 11 uncommitted analyzer files. The legacy GA comparison
mixes analyzer versions and is not comparable.

Retain scripts, paired commits/tree hashes, normalized-contract version, extractor
build identity, exclusions, failures, per-component results and fingerprints.
Reproduce against a recorded committed build before using percentages as targets.
Report potential fact matches and fully verified reuse separately; no hit-rate
promise is made. Reuse can only draw on snapshots produced by the new route
with verified dependency records, and legacy snapshots are never backfilled, so
the first version generated on the new route is a full-cost run. Savings begin
with the second version and grow as accepted snapshots accumulate; this is
accepted as planning for future releases. Record miss reasons, avoided synthesis calls, comparison/extraction
cost, structural repairs, evidence follow-ups, tokens, latency, unsupported claims,
coverage, preservation, merge outcomes, and consumer regressions. JSON may increase
storage/prompt size; avoid duplicate evidence and unnecessary schemas in prompts.

## Requirements traceability and superseded choices

References below are sections of the preserved original proposal unless linked
elsewhere. This table records the disposition of its requirements, including
deliberately replaced mechanisms.

| Original requirement or review decision | Disposition here |
|---|---|
| JSON construction, fact ownership, source provenance | Preserved: SC-01, SC-05 through SC-09 |
| Twelve published artifacts and separate manifest | Superseded by review consensus and user audit decision: four core files, SC-02/03 |
| Agent writes separate synthesis section files | Superseded: one response persisted by orchestrator; optional split run files, SC-10 |
| Model output stored only in logs | Superseded by user audit-retention requirement: permanent synthesis.json, SC-03 |
| Separate arch-doc renderer | Superseded: single analyzer renderer, optional compatibility wrapper, SC-04 |
| Candidate-based patch v1 and per-operation preconditions | Superseded on new route: typed values/fact IDs and one bundle fingerprint, SC-06; historical compatibility retained |
| Large upfront schema/publication phase | Superseded: deterministic first slice, followed by reuse; publication in phase 4 |
| Manifest marker and multi-file transaction machinery | Superseded: hash-linked authority, per-file atomicity, recoverable inputs and rerender, SC-17 |
| Coverage/read/insight/validation sidecars published individually | Superseded: detailed history in logs, essential knowledge/provenance in accepted core artifacts, SC-03/14/22 |
| Cross-version component reuse and no platform coupling | Required early: SC-11 through SC-16, phase 2 |
| Blind exclusion of evidence/cross-reference fields | Superseded by amended consensus item 3: SC-13 |
| Same-commit comparison as main reuse mechanism | Retained as fast path inside semantic/evidence verification, SC-11/12 |
| Supporting file and negative-search dependencies | Preserved and clarified: independent observations, real scope, stable content, SC-14 |
| Synthesis response participates in cache key | Explicitly excluded; response hash retained for integrity, SC-03/13/15 |
| Cross-analyzer compatibility ranges | Deferred; exact build/version compatibility first, SC-12/13 |
| Citation relocation and section-level invalidation | Deferred; whole-file hashes and whole-component reuse first |
| Prefixes, non-integrated Praxis, planned relationships | Preserved: SC-08/09/16/20 |
| Consumer Markdown, arch-query, platform/index/diagram support | Explicit obligations: SC-18 through SC-21; SC-18 sized and scheduled as a parallel track after phase 1 |
| Recorded source evidence versus true claims | Preserved distinction: SC-09/22/24 |
| Saved canary replay, no retroactive passing verdict | Preserved: SC-23/24 |
| Independent review, rollout hold, warning-only coverage, disabled workers | Preserved: phase gates and SC-22/24 |
| Recurring cost reduction versus structural simplification | Both explicit; reuse early and measured one-call synthesis, SC-10/11/24 |
| Codex snapshots not reuse-eligible until search telemetry is complete (consensus open item) | Made an explicit requirement: SC-25 |
| Diagram paths must be preserved for consumers | Superseded by user decision: diagrams have human readers only; relocation permitted |
| Tool-free single-call producer as the default (SC-10) | Superseded on the default route by ADR-0027: the existing agent loop emits the same response contract; tool-free retained opt-in |

## Execution and tracking

Under ADR-0027 the user may author the skill directly. Framework roles apply to
the Python adapter, defaults, flags, and independent review. Step 0 precedes any
implementation assignment.

Follow the [Implementation and Independent Review Framework](../notes/implementation-framework.md).
For this plan, Astra coordinates, Sol implements, and Fable 5.1 independently
reviews phase gates, with Opus 5 as the disclosed cost/availability fallback.
Record actual model identifiers and access at kickoff. Contract authors and
implementers cannot independently approve their own contributions. Track all
requirements SC-01 through SC-25 against source-verified evidence. Preserve
unrelated worktree changes and scope any future commit separately.

Use the framework's [CLI handoff protocol](../notes/implementation-framework.md#communication-and-cli-handoffs):
the coordinator launches bounded implementation and review assignments through
shell commands (`codex exec --model MODEL "assignment"` and
`claude -p --model MODEL "assignment"`). Claude's `-p` is print mode; Codex's
`-p` selects a profile. Verify actual CLI flags at kickoff, explicitly select
model/effort/permissions, and capture each attempt's prompt, result, stderr,
exit status, session identity, and evidence links. No direct agent messaging,
SDK integration, or new messaging service is required for plan execution.

Workers report questions, blockers, and completed evidence to the coordinator;
the implementation task records authoritative progress against SC-01 through
SC-25. Use disjoint file ownership and fresh reviewer sessions against recorded
input snapshots. Rate limits pause affected assignments and dependent gates
until capacity replenishes; resume the same model/settings. The Opus fallback
is not permitted for rate-limit-driven substitution. These are execution
instructions, not authorization to launch agents during this documentation edit
or to change the pipeline's product-level worker policy.

Use the [implementation task](../tasks/done/implement-structured-component-assembly.md)
for progress and record requirement-level evidence. Implementation completion,
live evaluation, and default-route adoption are distinct outcomes. Existing
[surface coverage decisions](architecture-surface-coverage.md) and
[patch migration history](../decisions/ADR-0019-versioned-json-architecture-patches.md)
remain relevant. This consolidation changes documentation only.
