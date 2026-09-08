# Analyzer lint gate has unresolved findings

Status: open. Observed 2026-09-07 during the SC-18 shared-validator follow-up.

The compatible cached golangci-lint v1.64.8 run over arch-analyzer reports eight
findings. Query lint and the new public validator package's scoped lint pass.
The analyzer findings must be reconciled before the final full lint gate; passing
Go tests/vet does not waive them.

- P1-added `internal/structured/patch.go`: unused `sortedDispositions`.
- P1-added `internal/structured/validate.go`: redundant nil/length evidence check.
- `internal/renderer/synthesis.go`: unused `deterministicArchitecturalAnalysis`
  and `partialCoverageNames`.
- `internal/gosource/mux_authentication.go`: unused `sortRepositoryRoutes`.
- `internal/extractor/categorycoverage.go`: simplifiable boolean return.
- `internal/gosource/behavioral_evidence_test.go`: ineffectual initial assignment.
- `internal/websource/websource.go`: deprecated `strings.Title`.

The last six findings' source constructs are present in the saved pre-P1 dirty
baseline. They are not introduced by the public-wrapper follow-up. The two
structured-package findings belong to P1 work and were not covered by its
test/vet gate. Do not label all eight as pre-task failures.

Evidence: `logs/structured-component-assembly/20260907-resume/`
`sc18-shared-validator/stdout.jsonl`, analyzer-wide lint command and result.
The pinned compatible tool is distinct from the unpinned `@latest` configuration
compatibility issue reported by the original SC-18 worker.

Repair in a bounded final-validation assignment after active frozen reviews, so
source changes cannot silently invalidate a review. Preserve existing behavior
and pre-existing edits; rerun relevant lint and tests with recorded tool identity.

## Implemented; independent review pending — 2026-09-08

Bounded Codex-only cleanup resolved these lint findings in local verification.
Normal `make lint` now passes, including pinned golangci-lint v1.64.8. Tests and
normal builds pass, with seven sandbox-blocked localhost tests rerun successfully
outside the sandbox. See
[coordinator report](../../../logs/structured-component-assembly/20260908-codex-only/coordinator-completion.md).
Keep this record open until the queued Claude review accepts the affected
changes; passing lint alone does not waive the parent gates.
