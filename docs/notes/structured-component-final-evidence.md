# Structured component P5 offline evidence

The final offline packet verifies format, preservation, recovery, consumers,
and conservative reuse behavior. It does not supply the missing live evidence
for default adoption.

## Conversion boundary

The replay is intentionally analyzer-only. It validates a legacy candidate's
heading structure, copies the saved analyzer facts, creates a synthesis
envelope whose state is `historical-response-missing`, normalizes the accepted
model, and renders Markdown with the current analyzer renderer. It never parses
the model-authored candidate into accepted facts. Unsupported legacy analyzer
fields, ambiguous legacy FIPS evidence, and FIPS headings outside `Security`
are explicit conversion errors.

The replay deliberately stops at the private schema-1.0 normalization/rendering
boundary. It does not claim to be a published schema-1.1 authority. P4's
independently accepted publication tests cover the four-file authority upgrade,
durable evidence/reuse bindings, log deletion, and recovery behavior.

That boundary preserves two important facts: the current renderer retains the
two baseline non-resource RBAC row names, but this does not repair the original
rejected promoted Markdown and does not show that an agent can emit schema
1.1. The four original source/proposal identities and rejected verdict remain
attached to the replay records. Original artifacts are not edited.

## Reuse result

The earlier `reuse-comparison.json` is retained byte-for-byte as interim failed
evidence. It only recounts the saved rows and falsely says the exact sources are
unavailable. The `checkouts` symlink resolves to `/data/checkouts`; all 184
recorded sides exist at the saved HEAD/tree. The two dirty
`models-perf-benchmark-data` working trees were replaced as object sources by
the coordinator's clean isolated copies, while all original checkouts remained
unchanged.

The old-build fresh run materialized only committed Git blobs, without checkout
filters or hooks, and retained repository origin, commit, and history in
isolated Git metadata. The minimal metadata intentionally has no Git index; the
analyzer enumerates the materialized filesystem. It recorded 12 gitlinks but
did not materialize their external submodule trees. All 184 extraction outputs
succeeded and unchanged `compare.py` compared all 92 pairs. Attempt 3 observed
31 legacy semantic-fact candidates and 37 current SC-13 analyzer-payload-only
matches; the independent cycle-1 rerun of the same inputs and binary observed
30 and 36. These are honestly retained samples from the old committed build,
whose unordered producer output made the unit counts unstable.

The repaired producer build is separately identified by binary SHA-256
`2ffc6dd7f567a941162cfa842cc7c20a5c8b4c56678b87073ffd90a9b5f92be8`
and complete analyzer source-manifest SHA-256
`86c1661ee978025117119934116c1777a84dfa1f70f16f8281f7f140844a6d40`.
Two independent processes freshly materialized and extracted all 184 source
sides. Every relevant output was identical, both runs produced 32 legacy
semantic-fact candidates and 38 current analyzer-payload-only matches, and all
92 pairs were compared. The latter diagnostic excludes `scan_statistics`; it
is not a complete SC-13 key. Blindly dropping all `version` keys remains an
unsupported sensitivity tier.

The repaired ordering changes are content-preserving. Compared with old-build
attempt 3, all changes in `security_evidence`, `integration_points`,
`entrypoints`, and `gap_evidence_index` are ordering-only; no source fact or
gap candidate changed. Normalization retained identical fact IDs,
dispositions, and sections for 184/184 sides. Rendering was byte-identical for
135 sides and changed only table-row order for 49; all rendered line multisets
were equal. In particular, kube-rbac-proxy imported two authorization packages
through a Go map and could alternate their security rows. The producer now
sorts Go import paths, Python script-table keys, platform resource and
OpenShift integration map keys, aggregate set-like entrypoint/integration
rows, security records/source sets, and complete gap-candidate tie-breakers.
Producer-local sorting happens before bounded gap selection, while final
aggregate sorting happens after it; this preserves producer-family priority
and the exact old candidate content. It does not sort
meaningful nested permissions, versions, conditions, commands, or other list
payloads.

The old committed analyzer binary is SHA-256
`458c04cb0387fe70b3dab8d5e0aedb88dccd0ee444d8cfc6bfce14ae6606f4e7`,
built with `-buildvcs=false` from the verified commit `e0f6f367` archive
SHA-256 `5f753cdb2ed40b3207c16985ca3dd83a839be578c8276bc31203e03bdfad4afa`.
This identity is separate from both the repaired dirty-source build above and
the saved historical analyzer at `39209078` plus 11 dirty source files. The
saved historical counts (11/33/38/40), old committed-build samples (31/37 and
30/36), and repaired-build result (32/38 twice) remain separately labeled.

Neither fresh extraction nor analyzer-fact equality supplies reads, searches,
component configuration/overlays, synthesis/model settings, an accepted
structured predecessor, or response identities. The complete SC-13 fingerprint
is therefore unavailable and verified reuse remains zero under SC-14/SC-25.
No percentage is a target or measured saving. Full evidence and both preserved
failed driver attempts are summarized in
`evaluations/structured-component-final/fresh-reuse/results.json`. Attempt 1
had 98 forced-selector failures plus 6 padded-gitlink parser failures, and its
dotted-name collision left 39 raw files per side for 40 internally compared
pairs. Attempt 3's 248.218 seconds is aggregate subprocess time: 218.0 seconds
came from carried attempt-2 records and 30.2 from its 10 new runs. Each repaired
validation run is instead 184 fresh subprocesses (251.861 and 251.063 aggregate
seconds), with no carry-forward.

## Adoption decision

Adoption is **HOLD**. The historical legacy canary provides historical
calls/tokens/latency and partial cost/quality observations only. No new-route
live model was run, so new-route cost, semantic quality, unsupported-claim
rate, follow-up frequency, and live schema compliance are unavailable. The
offline pipeline uses zero live model calls. Implementation/review harness use
is reported separately and is not pipeline runtime telemetry.

The proposed, unexecuted live packet is in
[structured-component-future-live-canary.md](structured-component-future-live-canary.md).
It requires separate model, cost, and execution authorization plus independent
review before any rollout decision.

## Rollback and retained policy

ADR-0025 remains the migration and rollback authority. Disable the opt-in
structured route to roll back; do not delete only `document.json`. Restore a
published four-file snapshot together from version control or let the tested
publication recovery protocol finish an interrupted replacement. Coverage
remains warning-only and subsection workers remain disabled under ADR-0023.
