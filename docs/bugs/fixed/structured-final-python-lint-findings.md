# Bug: Structured final Python lint findings

Status: open, non-blocking P2 follow-up.

F16 informational final-gate work: ruff finds I001 in tests/test_structured_component_model.py (P1-era; outside P2 delta) and five errors in evaluations/component-reuse-fingerprint/compare.py (pre-kickoff). P5 must resolve proportionately with evidence; full lint not yet passing.

Evidence: `logs/structured-component-assembly/20260907-resume/p2-review3-report.md`.

## Implemented; independent review pending — 2026-09-08

Bounded Codex-only cleanup resolved these lint findings in local verification.
Normal `make lint` now passes, including pinned golangci-lint v1.64.8. Tests and
normal builds pass, with seven sandbox-blocked localhost tests rerun successfully
outside the sandbox. See
[coordinator report](../../../logs/structured-component-assembly/20260908-codex-only/coordinator-completion.md).
Keep this record open until the queued Claude review accepts the affected
changes; passing lint alone does not waive the parent gates.

## Independent closure of this finding — 2026-09-08

Status: fixed. Fable/high cycle3 independently verified this finding's repair
against the current source; see
[review report](../../../logs/structured-component-assembly/20260908-review-resume/review-report.md).
This scoped closure does not approve P3: the separate SDK RPC quota error
F-P3-8 remains blocking. Documented runtime/authorization and offline-evidence
limits remain in force; historical incidents are not retroactively erased.
