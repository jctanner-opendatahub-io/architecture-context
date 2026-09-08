# Task: Review Structured Document Publishing and Consumers

Status: pending — P4 implementation and its evidence packet are not ready.
Depends on [P3 acceptance](review-structured-synthesis-final.md).
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

## Prepared test checklist

[Publication and consumer cases](../../notes/structured-publication-test-checklist.md)
were prepared during Codex-only work. They are required future checks, not
passing evidence or an implementation report.
