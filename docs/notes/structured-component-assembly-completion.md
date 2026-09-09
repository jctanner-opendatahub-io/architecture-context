# Structured component assembly — implementation completion

Completed 2026-09-09. The authorized implementation and offline validation
scope of the [consolidated plan](../plans/structured-component-assembly-consolidated.md)
is independently accepted. Live evaluation and default adoption remain **HOLD**.
The new generation route remains opt-in through `--structured-synthesis`.
No new commit or push was made during this completion.

## Delivered

- JSON construction and accepted document assembly, with one Markdown renderer
  and retained proposals, evidence and acceptance/rejection records.
- Whole-component reuse that checks relevant inputs and supporting observations,
  preserves provenance and makes no additional synthesis call on a verified hit.
- Bounded structured synthesis, explicit unresolved/failure states, and stopping
  on actual quota limits without model substitution.
- Four-file publication, recovery, mixed-format consumers, arch-query support,
  indexes, diagrams, lint and embedded packaging.
- Saved-canary replay, original-evidence preservation, fresh source comparisons,
  stable ordering for the observed producer collections and independent review.

## Final independent acceptance

P5 review cycle 2 completed after the user's rate-limit reset authorization.
Reviewer: `claude-fable-5-1`, high effort, resumed session
`b72d66cb-5ba6-4411-9dcb-7b7ec437700b`; exit 0 at
2026-09-09T15:35:29Z. The launcher also reports auxiliary Haiku usage; Fable
remained the gate reviewer. Cycle 3 was unused. The earlier rate-limited draft
and all rejected or superseded attempts remain preserved.

The [final report](../../logs/structured-component-assembly/20260909-ordering-review/review-report.md)
has SHA-256 `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
Its 9,717-file snapshot manifest has SHA-256
`c3a655ebd48ed0d47969c83ff24aa648a51edd4bdcfb0533e100401dafe8c4c9`.
The completed verdict is **PASS**, with no required findings remaining.

The final checks include 1,332 passing Python tests and 10 skips; all Go tests
and race checks; full lint; normal and embedded builds. The continuation retained
those completed checks by verified identity and additionally reran six ordering
tests three times each. Five old arch-query formatting listings remain a
documented nonblocking fact; required lint passes.

Three independent repaired-build runs cover the same 184 source versions and
92 pairs. Relevant output agrees across all three runs: 32 legacy fact matches,
38 current analyzer-only matches, and zero verified historical reuse. Missing
historical model/read/search records were not invented. Old committed-build
samples (31/37 and reviewer 30/36) remain labeled with their observed ordering
variation; new results do not replace their history.

The repaired analyzer binary SHA-256 is
`2ffc6dd7f567a941162cfa842cc7c20a5c8b4c56678b87073ffd90a9b5f92be8`.
It uses `-buildvcs=false` and a complete dirty-source manifest; it is not
identified by base commit `e0f6f367` alone. The old committed comparison build
`458c04cb…` and dirty P4 replay build `98fa820c…` retain their separate roles.

Fixed-input rendering and normalization match on all 184 inputs. With newly
ordered source output, 135 Markdown documents are byte-identical and 49 change
only row order, with no content loss. Fact IDs, dispositions and sections remain
unchanged. Position-derived `ordinal` and `input_pointer` values move with the
rows on 152 sides; those positions are not invariants.

The frozen evaluation matrix remains the implementer's reviewed proposal;
this completion record and the final report establish its final gate outcome.
SC-01–SC-23 and the required SC-25 fail-closed behavior are accepted within the
reviewed evidence and documented limits. SC-24 offline reporting and the HOLD
decision are accepted; live measurements remain unavailable. Optional complete
Codex search telemetry remains unimplemented, with explicit misses when needed.

## Remaining work and limits

The [separate live-canary task](../tasks/pending/evaluate-structured-component-live-canary.md)
requires execution, model and spending authorization. It will measure actual
quality, calls, tokens, latency and cost before a default-adoption decision.
The [future live packet](structured-component-future-live-canary.md) is prepared
but has not been executed. Coverage remains warning-only and subsection workers
remain disabled. ADR-0025 describes migration and rollback.

Nonblocking follow-ups remain open: rare analyzer input shapes with map-dependent
selection, error cleanup in the comparison materializer, existing query-number
and publication-repair edge cases, and outdated flag help. The verified corpus
does not establish universal determinism for every possible repository.
Go consumer validation does not independently recompute raw response identity
and producing-model eligibility; Python does. JSON-only typed queries work,
while a complete published package includes Markdown.

Detailed review packets are retained locally under ignored `logs/`; this durable
summary, task records and evaluation summaries do not imply those complete raw
packets were committed or pushed.
