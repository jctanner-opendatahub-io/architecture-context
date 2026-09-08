# Task: Finish Independent Review of Structured Synthesis

Status: pending — interrupted P3 cycle 3; waiting for user-authorized resumption
with Claude capacity. No verdict yet. Created 2026-09-08.

## Starting point

Complete the interrupted third review, not a new fourth cycle. The prior Claude
session `94728990-a54a-4230-9c86-e4edf303e620` stopped with HTTP 429 at
2026-09-08T16:44:42Z; reported reset was 3:30 p.m. America/New_York on that date.
This historical reset is not proof of current capacity.

Existing packet:

- [Full assignment](../../../logs/structured-component-assembly/20260907-resume/p3-review3-prompt.txt)
- [Checkpoint](../../../logs/structured-component-assembly/20260907-resume/p3-review3-rate-stop-checkpoint.json)
- [546-file manifest](../../../logs/structured-component-assembly/20260907-resume/p3-review3-inputs.json)
- [Previous review findings](../../../logs/structured-component-assembly/20260907-resume/p3-review2-report.md)
- [Claude repairs](../../../logs/structured-component-assembly/20260907-resume/p3-claude-repair2-report.md)
- [Codex repairs](../../../logs/structured-component-assembly/20260907-resume/p3-codex-repair2-report.md)
- [Test startup guard](../../../logs/structured-component-assembly/20260907-resume/p3-transport-guard-report.md)

The same run directory holds `p3-review3-source/`, `p3-review3.diff`,
`p3-review3-partial-evidence/`, and `p3-review-3/` invocation evidence.
Preserve them. Verify the manifest before resuming; if source has changed,
record the differences and prepare a new identified packet rather than applying
an old verdict to new code. Use a new scratch/output location and update the
saved assignment accordingly. The user cleared the Vim edit hold; Codex source
changes are included.

## Acceptance

Cover SC-03, SC-06, SC-07, SC-10, SC-14, SC-15, SC-22 and affected SC-11–SC-16/25
reuse guarantees. Follow the full assignment for all exact checks. In particular:

- Claude cannot add hidden response-repair calls through its JSON-output option.
- Requested and actual Codex models, defaults, settings, and local context are
  checked before reuse; changed meaningful inputs invalidate reuse.
- Both routes respect call limits, retain original answers and useful failure
  records, reject tool-active answers, and stop later calls on rate limits.
- The default offline test guard prevents real SDK startup; distinguish its
  tested coverage from the two earlier startup incidents and their uncertainties.
- Successful reuse makes zero synthesis calls; explicit unsupported settings
  and conservative misses are accurately documented, not called full support.

The 1,202 passing Python tests are supporting evidence, not independent approval.
If blocking findings remain after this final scheduled cycle, leave P3 open and
escalate under the parent budget; do not automatically schedule cycle 4.
P4 approval remains dependent on P3 acceptance.

## Review rules

Follow the [implementation framework](../../notes/implementation-framework.md)
and [consolidated plan](../../plans/structured-component-assembly-consolidated.md).
The [parent task](../current/implement-structured-component-assembly.md) owns
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
