# Structured component assembly checkpoint — 2026-09-08

This branch checkpoint saves the current implementation, tests, evaluation
records, and work ledger. It is not final independent acceptance or rollout
approval. The user explicitly authorized committing and pushing the current
changes to `regen/praxis-repos`; this supersedes earlier no-commit instructions
for this checkpoint only.

## State at the 2026-09-08 commit

Deterministic structured documents/rendering, bounded cross-version reuse, and
the arch-query adapter have earlier independent acceptance. The latest bounded
Claude/Codex synthesis changes and subsequent lint cleanup still await Claude
review. P3 cycle3 stopped at an actual Claude session limit without a verdict.
Publishing/collection integration (P4) and final acceptance/adoption evidence
(P5) remain open. Coverage remains warning-only, component workers remain
disabled, and the new structured synthesis route remains opt-in.

The later implementation and offline gates completed independent review on
2026-09-09; see [final completion](structured-component-assembly-completion.md).
That later work has not been committed or pushed by this task. Live evaluation
and default adoption remain HOLD.

## Local validation

The latest cleanup resolved six Python and eight analyzer lint findings. Both
Go checker invocations now pin golangci-lint v1.64.8. Full `make lint`, `make test`,
and normal `make build` pass. The complete Python run passed 1195 tests with 10
skips and seven sandbox socket setup errors. Those seven local mock-server tests
passed in a permitted targeted rerun, giving combined coverage of 1202 passed
and 10 skipped. The default test guard against actual model transport startup
remained enabled. These local checks do not replace independent review.

Twelve source/configuration files changed during the final cleanup; eleven overlap
the interrupted review packet. Historical generated results and rejected canary
verdicts are preserved. Formatting of the historical comparison utility is an
intentional source change; its original bytes are retained locally with verified
identity. Earlier reports retain the two accidental SDK startup incidents and
their uncertainties; this checkpoint does not erase that history.

## Review handoff and evidence availability

The [parent task](../tasks/done/implement-structured-component-assembly.md)
retains requirement and review history. Continue using these backlog tasks:

1. [Finish the interrupted P3 review](../tasks/done/review-structured-synthesis-final.md).
2. [Review P4 publication and consumers](../tasks/done/review-structured-publication-consumers.md).
3. [Review final checks and adoption hold](../tasks/done/review-structured-final-readiness.md).

The completed [offline preparation task](../tasks/done/prepare-structured-offline-checks.md)
and [publication test checklist](structured-publication-test-checklist.md)
record the Codex-only work. The same reviewer model/effort and existing phase
budgets apply. Do not infer approval from a checkpoint commit.

Detailed transcripts, frozen review source copies, and command logs remain in
ignored local `logs/structured-component-assembly/`; they are not included in
Git. A fresh clone has this summary and the tracked task/bug/evaluation records,
but needs those local evidence packets to reproduce the paused review exactly.
Do not treat links to local logs as remotely published review evidence.

The separately committed generated architecture directories are the existing
working-tree outputs, preserved without regeneration or hand editing. Saving
them is not a claim that the new publishing route is complete or newly approved.

## Later progress — P3 accepted, P4 underway

The preceding sections describe the pushed checkpoint, not the latest gate.
P3 completed independent review on 2026-09-08 at23:00Z: Fable/high session
`a6ccbff3-0617-487d-9223-2549189ce1f4` returned PASS, incorporating prior
reviews. The quota-error and diagnostic fixes are accepted. Independent full
Python1274 passed/10 skipped, focused283 and lint passed; no actual rate limit.
Evidence remains local in `logs/structured-component-assembly/20260908-quota-shapes/`.

P4 publishing and consumer integration is now running in direct Sol/high session
`01a0834d-053f-7403-b138-f743c6859eac`; packet `20260908-publication/`.
P4/P5 acceptance and live adoption remain open. These later changes are not a
newly pushed checkpoint, and no new commit/push has been requested.

### P4 accepted; P5 next — 2026-09-09 UTC

Fable/high b036fa12-9fc3-444a-ab72-fcc15280a655 completedP4 PASS at01:55:50Z,
auxiliaryHaiku disclosed,no actualrate.555sourcehashes match. FullPython1320pass
10skip, actualCLI readonly/ignorechecks pass; earlierGo/race/build/corpus/recovery
retainedbyidentity. Sixbugsclosed andP4reviewtaskdone. O1numericcanonicalization
andO7repairrace remainexplicitnonblockingbacklogs. O12recoveryalwaysrepairs even
repair_markdown=False noted; newreadonlyAPI separate. O13strayrecoveryfiles beside
validsnapshot passlint (cosmetic). O14corrects priorreport: five unchangedcommitted
arch-queryfiles appear in gofmt-l; arch-queryrequiredlintpasses, arch-analyzergofmt
gatepasses. No blanketclaimGoformatoutputempty. P5 finalofflineevidence next;
no livegeneration/adoption ornewcommit/push.
