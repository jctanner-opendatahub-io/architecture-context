# Task: Review Final Structured Assembly Checks and Adoption Hold

Status: pending — requires accepted P3/P4 and completed P5 offline evidence.
Depends on [P4 acceptance](review-structured-publication-consumers.md).
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
