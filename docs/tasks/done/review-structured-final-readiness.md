# Task: Review Final Structured Assembly Checks and Adoption Hold

Status: done — authorized implementation/offline scope independently accepted; live evaluation and adoption remain HOLD.
Depends on [P4 acceptance](../done/review-structured-publication-consumers.md).
Created 2026-09-08.

## Starting point

The [P5 handoff draft](../../../logs/structured-component-assembly/20260907-resume/p5-handoff-draft.txt)
is preparation only. Codex must supply the final source manifest/diff, full check
results, requirement matrix SC-01–SC-25, accepted phase reports, remaining bug
assessment, migration/rollback ADR, and offline comparison evidence before
review dispatch. Use the [existing requirements matrix](../../../logs/structured-component-assembly/20260906-kickoff/requirements.json)
as the starting record; update evidence/status without erasing earlier failures.

## Acceptance

- Independently verify consequential end-to-end claims and assess all required
  Python/Go tests, lint, builds, and embedded-package checks against final source.
  Account for the six known Python and eight analyzer lint findings; do not
  quietly exclude failing checks or treat an old passing build as current.
- Offline conversions preserve saved canary hashes and rejected verdicts.
  Unsupported legacy input fails clearly; conversion success is not proof that
  an AI model produces valid, accurate documents.
- Reuse comparisons identify the actual analyzer build and original baseline,
  distinguish possible matches from verified safe reuse, and do not invent
  missing source/search evidence.
- Every requirement has evidence and an honest status. Report implementation
  completion separately from live evaluation and default adoption.
- Keep SC-24 live cost/quality evaluation unavailable and adoption on HOLD until
  separately authorized and measured. Review a future bounded live-run packet
  if supplied; do not execute it or present estimated savings as measured results.
- Preserve warning-only coverage, disabled workers, historical evidence, and a
  usable rollback plan. No requirement or review gate is silently waived.

Return a final implementation verdict plus a separate adoption HOLD decision
with remaining conditions. Passing this offline gate does not close unmet live
SC-24 evidence. Route any substantive new repairs through independent review.

## Review rules

Follow the [implementation framework](../../notes/implementation-framework.md)
and [consolidated plan](../../plans/structured-component-assembly-consolidated.md).
The [parent task](implement-structured-component-assembly.md) owns
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

## Codex-only cleanup addendum — 2026-09-08

[Cleanup completion and review impact](../../../logs/structured-component-assembly/20260908-codex-only/coordinator-completion.md)
records 12 source/configuration edits, including 11 files in the paused P3 packet.
Use [current input hashes](../../../logs/structured-component-assembly/20260908-codex-only/cleanup-final-inputs.json)
and the linked deltas when preparing the resumed review. The old packet is
preserved but its worktree hashes are no longer current; do not blindly rerun
its assignment or claim its approval covers the cleanup. The 14 lint findings
now have passing local checks, still pending independent review. Historical
comparison-script formatting is the one intentional historical-manifest path
change; original bytes are retained and verified, and result data is unchanged.
The coordinator report also clarifies CLI timeout reconnections recorded during
worker launch. No rate-limit retry or reviewer substitution occurred.

## Latest entry reconciliation — 2026-09-09 UTC

P3 independently PASS (20260908-quota-shapes packet); the prior14lint findings
are independently fixed, including cycle3 cleanup impact. P4 cycle1 review now
runs against555frozen files in20260908-publication/. Refreshed P5 draft in that
packet removes the obsolete cleanup assignment and retains the exact historical
comparison-source exception. No P5 worker has launched; await P4 acceptance and
finalize current source identities before dispatch.

## Current preparation — 2026-09-09 UTC

P4 passed independent review in the `20260909-publication-repair` packet.
The initial P5 report did not reproduce extraction from available sources;
the coordinator rejected that completion claim before review. A direct
Sol/high continuation in `20260909-fresh-reuse/worker` is completing the
fresh comparison from recorded commits and a recorded committed analyzer build.
Preserve the initial report as superseded evidence. This task remains pending:
no P5 independent review has started and its first review cycle is unspent.

## Review dispatched — 2026-09-09 UTC

The continuation completed at 10:09:41 UTC, exit 0, no rate event. The final
comparison covers 184 source sides and 92 pairs, with 31 legacy fact matches
and zero verified reuse. Earlier driver failures remain saved. The product
baseline of 555 files is unchanged, and 83 affected tests plus Python lint pass.

Fresh Claude `claude-fable-5-1`, high effort, was launched through the standard
worker helper. Review cycle 1 of 3 is now in progress. Packet:
`logs/structured-component-assembly/20260909-fresh-reuse/review-cycle-1/`.
All 2,963 frozen input hashes verified before dispatch; manifest SHA-256:
`efb660f0e648cfd2a5929d587d454b5cca1435987dd15bdca3b393de867f069f`.
The reviewer must assess the three newly filed comparison bugs and the final
SC-01–SC-25 matrix. Implementation approval is pending; live SC-24 evidence
and default adoption remain on HOLD. No new commit or push occurred.

## Cycle 1 — REQUEST_CHANGES, 2026-09-09T10:27:22Z

Fable/high session `4d779de7-348b-4720-8325-55d82e5183bc` exited 0 with no
rate event. Launcher also reported auxiliary `claude-haiku-4-5-20251001` use;
the review model remained Fable. Independent full checks: 1330 Python passed,
10 skipped; Go tests/race/lint/build/embedded checks passed. All 2,963 frozen
hashes and 555 accepted product hashes remained unchanged.

F-P5-1: real analyzer output order varies, changing candidate counts and causing
spurious reuse misses. Coordinator selects a producer-ordering repair to meet
SC-11/13, with renewed review of affected P1 guarantees, not a deferral.
F-P5-2: future live packet conflates the replay and committed comparison builds.
Both findings are filed in the bug ledger; reports and historical samples stay
intact. Two final review cycles remain. See the cycle-1 report for accepted
bug-closure evidence and the byte-identical audit rewrite disclosure.

## Cycle 2 dispatched — 2026-09-09 UTC

Sol/high repair `01a085b7-fed8-7c00-809b-f3f3093a5b4b` exited 0 at
11:51:00 UTC, with no actual rate event. Final producer-local ordering repair
has two independent 184-source passes with identical relevant output, stable
32/38 candidate counts and no content loss. Both normal and embedded builds,
85 affected Python tests, all Go tests/race suites and full lint pass.
Intermediate bounded-selection approaches remain preserved and superseded.
The final dirty-source binary is `2ffc6dd7…`; old committed samples stay intact.

Fresh Fable/high cycle 2 launched in `20260909-ordering-review/reviewer`.
The 9,717-file manifest SHA is
`c3a655ebd48ed0d47969c83ff24aa648a51edd4bdcfb0533e100401dafe8c4c9`;
root verified every file before dispatch. The review renews affected analyzer,
rendering and reuse guarantees and assesses bounded evidence selection plus
build-reference corrections. No gate acceptance or live authorization implied.

## Rate-limit pause — 2026-09-09T12:26:36Z

Fable/high session `79b9135b-098b-4c27-a207-e8d0738a68ee` exited 1, API 429,
session limit, provider reset 11:10 a.m. America/New_York (15:10 UTC).
Stopped without retry or substitution. Launcher reports auxiliary Haiku usage.
Cycle 2 remains unfinished; cycle 3 is unused. The draft proposes PASS and
records 1332 passing Python tests, 10 skips, all Go/race/lint/build checks and
a complete independent 184-side run, but no final report was published.
Do not treat the draft or pause as gate acceptance.

Saved checkpoint and unchanged draft:
`logs/structured-component-assembly/20260909-ordering-review/rate-limit-checkpoint.md`
and `review-report-draft-rate-limited.md`. Two provisional nonblocking follow-ups
were filed (rare map-order selection and materialization-error deadlock).
No post-limit repairs or bug closures occurred. Resume this same review cycle
with Fable/high after user continuation and restored quota, checking unchanged
inputs and completing the final verdict before task/bug closure. Live/adoption
remain HOLD.

## User-authorized review continuation — 2026-09-09

User reports Claude quota reset and requests continuation. Root verified all
9,717 frozen file hashes unchanged, then launched a bounded fresh Fable/high
continuation in `20260909-ordering-review/reviewer-resume`. This completes the
interrupted second review cycle; it is not a third cycle or a model substitution.
The assignment reconciles the preserved draft with completed independent
evidence and requires a published final verdict. No live execution is authorized.

## Final acceptance — 2026-09-09T15:35:29Z

Fresh Fable/high continuation `b72d66cb-5ba6-4411-9dcb-7b7ec437700b` completed interrupted P5
cycle 2 with PASS, exit 0 and no further rate event. Launcher records
auxiliary Haiku usage; Fable remained the gate reviewer. Cycle 3 unused.
Final report: `logs/structured-component-assembly/20260909-ordering-review/review-report.md`, SHA-256 `fe29c90dfc21056dbc190679ba4103cb57027108470cbfc700dc179a36d5f0e9`.
All 9,717 reviewed file hashes remained unchanged. Retained independent
checks: 1,332 Python passes/10 skips; all Go/race/lint/build/embedded
checks pass; independent 184-source reproduction matches both worker
runs, with no fact loss. Same-model continuation additionally reran
six ordering tests three times each. No required finding remains.

Five bugs were closed from explicit criterion acceptance. Nonblocking
rare map-order input shapes and materialization-error cleanup remain
backlog. SC-24 live quality/cost evaluation and default adoption remain
unmeasured/HOLD; the route stays opt-in. See the completion note and
separate pending live-canary task. No new commit or push.
