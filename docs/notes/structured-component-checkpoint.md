# Structured component assembly checkpoint — 2026-09-08

This branch checkpoint saves the current implementation, tests, evaluation
records, and work ledger. It is not final independent acceptance or rollout
approval. The user explicitly authorized committing and pushing the current
changes to `regen/praxis-repos`; this supersedes earlier no-commit instructions
for this checkpoint only.

## Current state

Deterministic structured documents/rendering, bounded cross-version reuse, and
the arch-query adapter have earlier independent acceptance. The latest bounded
Claude/Codex synthesis changes and subsequent lint cleanup still await Claude
review. P3 cycle3 stopped at an actual Claude session limit without a verdict.
Publishing/collection integration (P4) and final acceptance/adoption evidence
(P5) remain open. Coverage remains warning-only, component workers remain
disabled, and the new structured synthesis route remains opt-in.

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

The [parent task](../tasks/current/implement-structured-component-assembly.md)
retains requirement and review history. Continue using these backlog tasks:

1. [Finish the interrupted P3 review](../tasks/pending/review-structured-synthesis-final.md).
2. [Review P4 publication and consumers](../tasks/pending/review-structured-publication-consumers.md).
3. [Review final checks and adoption hold](../tasks/pending/review-structured-final-readiness.md).

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
