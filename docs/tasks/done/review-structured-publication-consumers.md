# Task: Review Structured Document Publishing and Consumers

Status: pending — P4 implementation and its evidence packet are not ready.
Depends on [P3 acceptance](../done/review-structured-synthesis-final.md).
Created 2026-09-08.

## Starting point

Review P4 after Codex has completed and tested the implementation. The existing
[P4 handoff draft](../../../logs/structured-component-assembly/20260907-resume/p4-handoff-draft.txt)
is preparation, not evidence that the work exists. Before dispatch, attach the
implementation report, exact source manifest/diff, test outputs, migration ADR,
open findings, and accepted P3/P2/arch-query dependencies. Reassess any changes
to previously approved contracts. Review only the completed, identified packet.

## Acceptance

Cover SC-02, SC-08, SC-09, SC-17–SC-23 and cross-phase SC-03/15 retention:

- Publishing produces the four core files; original AI answers, source evidence,
  decisions, and reuse eligibility survive removal of logs and private run files.
- Interruptions between file replacements are detected. Prior accepted output
  survives failure, and recovery restores consistent documents without AI calls.
  Check actual Markdown contents, not just a copied hash marker.
- arch-query, flat Markdown readers, indexes, platform summaries, diagrams,
  both collectors, audits, and release/embedded packages recognize the layout.
  Invalid new documents fail clearly; metadata is not counted as components.
- Test actual renderer output, mixed old/new documents, JSON-only queries,
  missing Markdown paths, prefixes, Praxis inclusion, RBAC, uncertainty,
  human corrections, citations, and planned versus current relationships.
- Migration and rollback are explicit. Unsupported legacy fields and malformed
  FIPS placement fail without silent data loss. Historical outputs are unchanged.

Independently exercise crash recovery, audit retention after log removal, and
representative consumer integration. Retain prior arch-query acceptance only
where its inputs/guarantees still apply. No live generation is needed for this
gate. P5 final approval depends on accepted P4 evidence.

## Review rules

Follow the [implementation framework](../../notes/implementation-framework.md)
and [consolidated plan](../../plans/structured-component-assembly-consolidated.md).
The [parent task](../done/implement-structured-component-assembly.md) owns
implementation status, review history, and the three-cycle-per-phase escalation
budget. These tasks organize the remaining gates; they do not reset that budget.

Owner: independent Claude reviewer, exact `claude-fable-5-1`, high effort.
Codex coordinates and repairs findings; it cannot approve its own contributions.
Use `scripts/run_implementation_worker.py` with a saved bounded assignment and
new attempt directory. Record requested/resolved model, session, source hashes,
commands, results, findings, limitations, and PASS / REQUEST_CHANGES / BLOCKED.
Inspect actual source and independently test consequential claims. Reviewers
write review evidence, not replacement implementations. The coordinator files
bugs and updates the ledger. Move pending → current when dispatched; move to
done only after acceptance, or blocked with the reason when necessary.

Stop on any actual rate limit; preserve evidence and resume only on user
continuation with the same model/effort. No automatic retries, substitutions,
or waived gates. No live pipeline/model tests, publishing, default adoption,
commits, or historical generated-output rewrites are authorized by this task.
Offline tests must prevent authenticated SDK startup. Preserve failed evidence.

## Prepared test checklist

[Publication and consumer cases](../../notes/structured-publication-test-checklist.md)
were prepared during Codex-only work. They are required future checks, not
passing evidence or an implementation report.

## P4 cycle1 review underway — 2026-09-09 UTC

Status: current. Sol/high session01a0834d-053f-7403-b138-f743c6859eac completed
implementation at00:48:50Z, no rate.37owned paths verified,555source/doc/test files
frozen with exact delta in `logs/structured-component-assembly/20260908-publication/`.
70 selected command outputs retained including development failures. Focused
recovery includes26boundaries; affectedPython/Go/vet/race/build-embedded pass.
FullPython1309pass10skip7socketerrors plus coordinator7socketpass predates the
final small publication/test delta; reviewer will check final bytes. Coordinator
default pinned Golint passes. Fresh Fable/high review actually launched against
this packet. Three-cycle P4 budget, cycle1; P3's extra cycles do not reset it.
No acceptance claimed, no livegeneration/adoption/commit. Development linter
import bug remains open pending independent acceptance.

### P4 cycle1 REQUEST_CHANGES; focused repair proceeds within budget

Fable/high sessiona5d91853-a159-43d6-8187-97ba233134c9 exited0 at01:12:18Z,
auxiliaryHaiku disclosed, no actual rate. All555sourcehashes unchanged. Full
Python1317pass10skip, fullGo/vet/race/lint/embedded and26recoveryboundaries pass.
Two blockers: F-P4-1 broadignorepattern hides futurelegacy sidecars; F-P4-2 lint
mutates staleMarkdown and createslocks instead of rejecting read-only. Bothfiled,
plus nonblocking numeric-canonicalization and repair-race backlogs. Report/evidence
saved20260908-publication/. Existing queryexists/purpose/predecessor fixes meet
criteria, closure waits focusedrepairreview. Linterimport fixed but remainsopen
untilF-P4-2. Cycle2 repair/review authorized by original3cycleP4 budget.

SC04 interface disposition independentlyaccepted: legacy arch-doc cannot consume
structured document and remains only legacy assembler while those callers remain;
all structured rendering delegates shared analyzer renderer. O2 requires ADR
clarification: Go query/Stage do not independently recompute rawresponse identity
or producingmodel eligibility; Python producer/reuse checks do. Packaging requires
completeMarkdown although typedqueries supportJSONonly. Deterministic-only is a
tested library state, no migrationpipelinecaller; live/defaultadoption stillHOLD.

### Focused cycle2 implementation launched

Actual direct Sol/high invocation in
`logs/structured-component-assembly/20260909-publication-repair/` against555
verified source identities. Scope F-P4-1/F-P4-2 and O2/O3 documentationclarity;
no Go redesign or unrelated nonblockingbug expansion. Fresh Fable/high review
follows final implementation/evidence. No source acceptance or rate-limit event.

### Cycle2 repair complete; fresh review actually launched — 01:37Z

Sol/high01a083be-84d2-7fd0-9f78-4894a19769c5 exited0 at01:36:25Z, no rate.
Eightreportedpaths verified;555frozenfiles and focused delta in20260909-publication-repair/.
F1ignore narrow; F2readonly validation path/actualCLI tests; O2/O3docsclarified.
Focused7+169pass, full1313pass10skip7sandboxsocketerrors; Go248pathsunchanged
fromindependentlypassingcycle1. FreshFable/high review launched; P4 notyetaccepted.

## Complete — P4 PASS at2026-09-09T01:55:50Z

Fable/high sessionb036fa12-9fc3-444a-ab72-fcc15280a655, auxiliaryHaiku disclosed,
no actualrate. Eightrepairfiles and555finalsourcehashes verified.1320Pythonpass,
10skip, readonlylint/ignore tests pass. Cycle1broadGo/race/build/consumer/recovery
acceptance retainedbyidentity. Sixbugsclosed. Numericcanonicalization andrepair
race remainnonblockingbacklog. SC04legacyarch-docinterface explicitlyaccepted;
O2Go eligibilitylimit andO3JSONonly/packageasymmetry documented andaccepted.
P5 final/offlineevidence andliveadoption remainseparate. Cycle2of3closedP4.
Evidence: logs/structured-component-assembly/20260909-publication-repair/.
